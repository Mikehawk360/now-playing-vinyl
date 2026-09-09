' MainScene logic.
'
' For now this just styles the placeholder label. The polling loop that
' fetches now-playing JSON from the relay and displays album art will be
' added here later (see CLAUDE.md).
sub init()
    m.statusLabel = m.top.findNode("statusLabel")
    m.statusLabel.font = "font:LargeBoldSystemFont"
    m.top.setFocus(true)
end sub
