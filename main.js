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

    function loadURL() {
        win.loadURL('http://localhost:5000').catch((err) => {
            console.error('Failed to load http://localhost:5000, retrying in 1 second', err);
            setTimeout(loadURL, 1000);
        });
    }

    loadURL();

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