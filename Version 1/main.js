const { app, BrowserWindow } = require('electron')
const http = require('http')
const child_process = require('child_process')
const path = require('path')

let win;
let flaskServer;

function createWindow () {
    win = new BrowserWindow({
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

    win.on('closed', function () {
        if (flaskServer != null) {
            flaskServer.kill();  // Stop the Flask server
        }
    });
}

app.whenReady().then(() => {
    // Paths for the Flask servers
    const flaskExecutableDev = 'app.py'; // Development server
    const flaskExecutableExe = 'app.exe'; // Exe server checker
    const flaskExecutablePackaged = path.join(process.resourcesPath, 'app.exe');

    // Choose the Flask server to use
    const flaskExecutable = flaskExecutablePackaged; // Switch this line to use a different server

    // Start the Flask server 
    flaskServer = child_process.spawn(flaskExecutable);

    createWindow();
});