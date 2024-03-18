const { app, BrowserWindow } = require('electron')
const http = require('http')

function createWindow () {
    let win = new BrowserWindow({
        webPreferences: {
            nodeIntegration: true,
        },
        show: false // initially hidden
    })

    win.once('ready-to-show', () => {
        win.maximize() // maximize when ready to show
    })

    win.loadURL('http://localhost:5000')

    win.webContents.on('new-window', function(event, url) {
        event.preventDefault()
        let newWin = new BrowserWindow({ show: false }) // initially hidden
        newWin.once('ready-to-show', () => {
            newWin.maximize() // maximize when ready to show
        })
        newWin.loadURL(url)
    })
}

app.whenReady().then(createWindow)