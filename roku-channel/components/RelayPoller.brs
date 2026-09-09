' RelayPoller task: poll <relayUrl>/now-playing forever, publish the
' parsed record on m.top.nowPlaying (only when the body changes) and
' keep m.top.reachable current.

sub init()
    m.top.functionName = "pollLoop"
end sub

sub pollLoop()
    interval = m.top.pollInterval
    if interval < 2 then interval = 2

    m.lastBody = ""

    while true
        fetchOnce()
        sleep(interval * 1000)
    end while
end sub

sub fetchOnce()
    url = m.top.relayUrl
    if url = invalid or url = "" then
        m.top.reachable = false
        return
    end if

    xfer = CreateObject("roUrlTransfer")
    xfer.setUrl(url + "/now-playing")
    xfer.setRequestType("GET")
    xfer.enableEncodings(true)
    ' Needed only for https relays; harmless for http.
    xfer.setCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.initClientCertificates()

    port = CreateObject("roMessagePort")
    xfer.setPort(port)

    body = invalid
    if xfer.asyncGetToString()
        msg = wait(5000, port)  ' 5s timeout so a stalled relay can't hang the loop
        if type(msg) = "roUrlEvent"
            if msg.getResponseCode() = 200 then body = msg.getString()
        else
            xfer.asyncCancel()
        end if
    end if

    if body = invalid then
        m.top.reachable = false
        return
    end if

    m.top.reachable = true

    if body = m.lastBody then return  ' unchanged, don't re-notify
    m.lastBody = body

    parsed = ParseJSON(body)
    if parsed = invalid then return
    m.top.nowPlaying = parsed
end sub
