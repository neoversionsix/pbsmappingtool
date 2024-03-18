const { app, BrowserWindow } = require('electron')
const http = require('http')

function createWindow () {
    let win = new BrowserWindow({
        webPreferences: {
            nodeIntegration: true,
        },
        fullscreen: true
    })

    win.loadURL('http://localhost:5000')

    win.webContents.on('new-window', function(event, url) {
        event.preventDefault()
        let newWin = new BrowserWindow({ fullscreen: true })
        newWin.loadURL(url)
    })
}

app.whenReady().then(createWindow)