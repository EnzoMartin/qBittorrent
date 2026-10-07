/*
 * Bittorrent Client using Qt and libtorrent.
 * Copyright (C) 2026  EnzoMartin/qBittorrent fork maintainer
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give permission to
 * link this program with the OpenSSL project's "OpenSSL" library (or with
 * modified versions of it that use the same license as the "OpenSSL" library),
 * and distribute the linked executables. You must obey the GNU General Public
 * License in all respects for all of the code used other than "OpenSSL".  If you
 * modify file(s), you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete this
 * exception statement from your version.
 */

#include "peerconnectionlog.h"

#include <chrono>
#include <map>
#include <string>
#include <string_view>
#include <tuple>

#include <libtorrent/alert_types.hpp>
#include <libtorrent/operations.hpp>

#include <QString>

#include "base/logger.h"

namespace
{
    // Consumers parse log/main for this prefix; changing it breaks them.
    const QString PREFIX = QStringLiteral("peer-connection: ");

    using Clock = std::chrono::steady_clock;
    constexpr auto WINDOW = std::chrono::seconds(60);
    // The endpoint is never part of the key: the remote side controls it, so it would grow the map without bound.
    constexpr std::size_t MAX_KEYS = 48;

    struct Key
    {
        int alertType;
        int op;
        std::string category;
        int value;

        bool operator<(const Key &other) const
        {
            return std::tie(alertType, op, category, value) < std::tie(other.alertType, other.op, other.category, other.value);
        }
    };

    struct Window
    {
        Clock::time_point start;
        long suppressed = 0;
    };

    // Only ever touched from on_alert, which libtorrent calls under its alert-manager mutex.
    std::map<Key, Window> windows;
    long connects = 0;

    bool isSsl(const lt::error_code &error)
    {
        return std::string_view(error.category().name()) == "asio.ssl";
    }
}

void logPeerConnectionAlert(const lt::alert *alert)
{
    int op = 0;
    lt::error_code error;
    switch (alert->type())
    {
    case lt::peer_connect_alert::alert_type:
        ++connects;
        return;
    case lt::peer_error_alert::alert_type:
        {
            const auto *peerError = static_cast<const lt::peer_error_alert *>(alert);
            op = static_cast<int>(peerError->op);
            error = peerError->error;
        }
        break;
    case lt::peer_disconnected_alert::alert_type:
        {
            const auto *disconnected = static_cast<const lt::peer_disconnected_alert *>(alert);
            if ((disconnected->op != lt::operation_t::connect) && !isSsl(disconnected->error))
                return;
            op = static_cast<int>(disconnected->op);
            error = disconnected->error;
        }
        break;
    default:
        return;
    }

    Key key {alert->type(), op, error.category().name(), error.value()};
    if ((windows.size() >= MAX_KEYS) && (windows.find(key) == windows.end()))
        key = Key {-1, -1, "overflow", 0};

    const auto now = Clock::now();
    long suppressed = 0;
    const auto [it, inserted] = windows.try_emplace(key, Window {now, 0});
    if (!inserted)
    {
        if ((now - it->second.start) < WINDOW)
        {
            ++it->second.suppressed;
            return;
        }
        suppressed = it->second.suppressed;
        it->second = Window {now, 0};
    }

    QString line = PREFIX + QString::fromStdString(alert->message())
        + QStringLiteral(" (connects since start: %1").arg(connects);
    if (suppressed > 0)
        line += QStringLiteral("; %1 more like this suppressed in the last minute").arg(suppressed);
    line += u')';
    LogMsg(line, (isSsl(error) ? Log::WARNING : Log::INFO));
}
