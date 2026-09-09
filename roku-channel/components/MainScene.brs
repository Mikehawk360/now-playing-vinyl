' MainScene logic.
'
' Starts a RelayPoller task, then reacts to its output: shows the album
' art Poster when a record is playing, or the status Label otherwise.

sub init()
    m.art = m.top.findNode("art")
    m.statusLabel = m.top.findNode("statusLabel")
    m.statusLabel.font = "font:MediumBoldSystemFont"

    info = CreateObject("roAppInfo")
    relayUrl = info.GetValue("relay_url")
    pollInterval = info.GetValue("poll_interval_seconds").ToInt()
    if pollInterval <= 0 then pollInterval = 10

    m.currentArtUrl = ""
    showStatus("Waiting for music...")

    m.art.observeField("loadStatus", "onArtLoadStatus")

    m.poller = CreateObject("roSGNode", "RelayPoller")
    m.poller.relayUrl = relayUrl
    m.poller.pollInterval = pollInterval
    m.poller.observeField("nowPlaying", "onNowPlaying")
    m.poller.observeField("reachable", "onReachable")
    m.poller.control = "RUN"

    m.top.setFocus(true)
end sub

' New now-playing record from the relay.
sub onNowPlaying()
    np = m.poller.nowPlaying

    artUrl = ""
    if np <> invalid and np.artUrl <> invalid then
        artUrl = np.artUrl
    end if

    if artUrl = "" then
        m.currentArtUrl = ""
        m.art.uri = ""
        showStatus("Waiting for music...")
        return
    end if

    if artUrl = m.currentArtUrl then return  ' same art, nothing to do

    m.currentArtUrl = artUrl
    m.art.uri = artUrl  ' onArtLoadStatus swaps visibility once it loads
end sub

' Poster finished (or failed) loading the image.
sub onArtLoadStatus()
    if m.currentArtUrl = "" then return  ' we cleared it on purpose

    status = m.art.loadStatus
    if status = "ready" then
        m.statusLabel.visible = false
        m.art.visible = true
    else if status = "failed" then
        showStatus("Album art didn't load")
    end if
end sub

' Relay reachability changed.
sub onReachable()
    if not m.poller.reachable and m.currentArtUrl = "" then
        showStatus("Can't reach the relay...")
    end if
end sub

sub showStatus(text as string)
    m.statusLabel.text = text
    m.statusLabel.visible = true
    m.art.visible = false
end sub
