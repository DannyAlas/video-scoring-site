import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.0.0/firebase-app.js'

// If you enabled Analytics in your project, add the Firebase SDK for Google Analytics
import { getAnalytics } from 'https://www.gstatic.com/firebasejs/10.0.0/firebase-analytics.js'

// Add Firebase products that you want to use
import { getAuth, GoogleAuthProvider, signInWithPopup } from 'https://www.gstatic.com/firebasejs/10.0.0/firebase-auth.js'
import { getFirestore } from 'https://www.gstatic.com/firebasejs/10.0.0/firebase-firestore.js'
// Initialize Firebase
const firebaseConfig = {
    apiKey: "AIzaSyAJgxzDc4R8O-0K2ERniiWSbeCIvyemw24",
    authDomain: "video-scoring-7d4f4.firebaseapp.com",
    projectId: "video-scoring-7d4f4",
    storageBucket: "video-scoring-7d4f4.appspot.com",
    messagingSenderId: "1001007622730",
    appId: "1:1001007622730:web:9dfcf5dabdb26c705214b3",
    measurementId: "G-KK7GJJ1B6S"
};
// set the global variables
var CURRENT_VIDEO_ID = null
var CURRENT_VIDEO_FPS = 30
var IS_ONSET = true
var user = null
const app =  initializeApp(firebaseConfig);
const contextMenu = document.getElementById("context-menu");
contextMenu.classList.remove("visible");  
        
// if the user is logged in, update the navbar
var xhr = new XMLHttpRequest()
xhr.open('GET', '/api/user', true)
xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
xhr.onload = function() {
    if (xhr.status === 200) {
        var user = JSON.parse(xhr.responseText)
        document.getElementById('profileIcon').src = user.photoUrl
              
        
        // a function that gets the timestamps for a video
        function getTimestamps() {
            if (CURRENT_VIDEO_ID === null) {
                alert("Please select a video")
            } else {
                var xhr = new XMLHttpRequest()
                xhr.open('GET', '/api/timestamps/' + CURRENT_VIDEO_ID, true)
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        var timestamp_doc = JSON.parse(xhr.responseText)
                        var timestamps = timestamp_doc.ts
                        var timestampsTable = document.getElementById("timestampList")
                        // clear the table
                        timestampsTable.innerHTML = ""
                        // add each timestamp to the table
                        timestamps.forEach(function(timestamp) {
                            var row = timestampsTable.insertRow(-1)
                            var onset = row.insertCell(0)
                            var offset = row.insertCell(1)
                            onset.innerHTML = timestamp.split(",")[0]
                            offset.innerHTML = timestamp.split(",")[1]
                        })
                    }
                }
                xhr.send()
            }
        }        
        
        // post request to the server to set the timestamps for a video
        function setTimestamps() {
            // post the timestamps to the server
            var timestamps = document.getElementById("timestampList")
            var ts_arr = []
            // for row in table add a string to the array of onset,offset
            for (let i = 0; i < timestamps.rows.length; i++) {
                var row = timestamps.rows[i]
                var onset = row.cells[0].innerHTML || ""
                if (row.cells.length > 1) {
                    var offset = row.cells[1].innerHTML
                } else {
                    var offset = ""
                }
                ts_arr.push(onset + "," + offset)
            }
            // post the timestamps to the server
            var xhr = new XMLHttpRequest()
            xhr.open("POST", '/api/timestamps/' + CURRENT_VIDEO_ID, true)
            xhr.setRequestHeader('Content-Type', 'application/json')
            xhr.send(JSON.stringify(ts_arr))
        }

        // a function to get the video list
        function getVideoList() {
            var xhr = new XMLHttpRequest()
            xhr.open('GET', '/api/videos', true)
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var videos = JSON.parse(xhr.responseText)
                    var videoList = document.getElementById("videoList")
                    // clear the table
                    videoList.innerHTML = ""
                    // add each video to the table
                    videos.forEach(function(video) {
                        var row = videoList.insertRow(-1)
                        var videoID = row.insertCell(0)
                        var complete = row.insertCell(1)
                        var scorers = row.insertCell(2)
                        videoID.innerHTML = video.id
                        complete.innerHTML = video.completed
                        scorers.innerHTML = video.scorers.join(", ") || "None"
                        // event listener for when a video is clicked
                        row.addEventListener("click", function() {
                            CURRENT_VIDEO_ID = video.id
                            // update the video player
                            var videoPlayer = document.getElementById("videoPlayer")
                            videoPlayer.src = "/video/" + video.id + ".mp4"
                            videoPlayer.load()
                            // update the video name
                            var videoName = document.getElementById("playerTitle")
                            videoName.innerHTML = video.id
                            // update the video list
                            var videoList = document.getElementById("videoList")
                            var rows = videoList.getElementsByTagName("tr")
                            for (var i = 0; i < rows.length; i++) {
                                rows[i].style.backgroundColor = "white"
                            }
                            row.style.backgroundColor = "#e6e6e6"
                            // update the timestamps
                            getTimestamps(video.id)

                        })
                    })
                }
            }
            xhr.send()
        }
        
        // a function to populate the keybindings table
        function getKeybindings() {
            // to the keybindings table add the keybindings
            var keybindingsTable = document.getElementById("keybindingsTable")
            keybindingsTable.innerHTML = ""
            // get the keybindings from the server
            var xhr = new XMLHttpRequest()
            xhr.open('GET', '/api/user/keybindings', true)
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var KEYBINDINGS = JSON.parse(xhr.responseText)
                    // add each keybinding to the table
                    KEYBINDINGS.forEach(function(keybinding) {
                        var row = keybindingsTable.insertRow(-1)
                        var key = row.insertCell(0)
                        var action = row.insertCell(1)
                        // convert the keybindings key to a string
                        var keybindingString = ""
                        if (keybinding.key.ctrlKey) {
                            keybindingString += "Ctrl + "
                        }
                        if (keybinding.key.shiftKey) {
                            keybindingString += "Shift + "
                        }
                        if (keybinding.key.altKey) {
                            keybindingString += "Alt + "
                        }
                        if (keybinding.key.metaKey) {
                            keybindingString += "Meta + "
                        }
                        keybindingString += keybinding.key.key.toUpperCase()
                        // if the keybinding is the spacebar, display it as "Space"
                        if (keybindingString === " ") {
                            keybindingString = "Space"
                        }
                        key.innerHTML = keybindingString
                        action.innerHTML = keybinding.action
                    })
                }
            }
            xhr.send()
        }

        // an event for the logout button
        document.getElementById("logoutLink").addEventListener("click", function() {
            var xhr = new XMLHttpRequest()
            xhr.open("GET", "/logout", true)
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
            xhr.onload = function() {
                if (xhr.status === 200) {
                    // remove session cookies
                    document.cookie = "session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"
                    window.location.href = "/"
                }
            }
            xhr.send()
        })

        // an eventlister for the spacebar to which will add the current video timestamp to the table
        document.addEventListener("keydown", function(e) {
            // arrow keys move the video forward and backward one frame
            if (e.keyCode === 37) {
                e.preventDefault()
                var video = document.getElementById("videoPlayer")
                video.currentTime -= (1 / CURRENT_VIDEO_FPS) * NUMER_OF_FRAMES_TO_SKIP
            } else if (e.keyCode === 39) {
                e.preventDefault()
                var video = document.getElementById("videoPlayer")
                video.currentTime += (1 / CURRENT_VIDEO_FPS) * NUMER_OF_FRAMES_TO_SKIP
            } 
            if (e.shiftKey) {
                    if (e.keyCode === 37) {
                        e.preventDefault()
                        var video = document.getElementById("videoPlayer")
                        video.currentTime -= 1
                    } else if (e.keyCode === 39) {
                        e.preventDefault()
                        var video = document.getElementById("videoPlayer")
                        video.currentTime += 1
                    }
            }
            // if the s key is pressed, save the timestamps
            if (e.keyCode === 83) {
                e.preventDefault()
                if (CURRENT_VIDEO_ID === null) {
                    return
                } else {
                    // get the current video time
                    var video = document.getElementById("videoPlayer")
                    var time = video.currentTime
                    // add the timestamp to the table
                    var timestampsTable = document.getElementById("timestampList")
                    if (IS_ONSET) {
                        var row = timestampsTable.insertRow(-1)
                        var onset = row.insertCell(0)
                        var offset = row.insertCell(1)
                        IS_ONSET = false
                        onset.innerHTML = time
                        offset.innerHTML = ""
                        setTimestamps()
                    } else {
                        var row = timestampsTable.rows[timestampsTable.rows.length - 1]
                        var offset = row.cells[1]
                        IS_ONSET = true
                        // check if the offset is greater than the onset
                        if (time < parseFloat(row.cells[0].innerHTML)) {
                            alert("Offset must be greater than onset")
                            return
                        }
                        offset.innerHTML = time
                        setTimestamps()
                    }
                }
            }
            // if ctrl+z is pressed, undo the last timestamp
            if (e.keyCode === 90 && e.ctrlKey) {
                e.preventDefault()
                var timestampsTable = document.getElementById("timestampList")
                if (timestampsTable.rows.length > 0) {
                    if (IS_ONSET) {
                        // delete the last row
                        timestampsTable.deleteRow(timestampsTable.rows.length - 1)
                        IS_ONSET = false
                        setTimestamps()
                    } else {
                        // delete the offset
                        var row = timestampsTable.rows[timestampsTable.rows.length - 1]
                        row.deleteCell(1)
                        IS_ONSET = true
                        setTimestamps()
                    }
                }
            }
        })

        // an event listener when a timestamp is clicked, will set the video time to the timestamp
        document.getElementById("timestampList").addEventListener("click", function(e) {
            if (e.target.tagName === "TD") {
                var video = document.getElementById("videoPlayer")
                video.currentTime = e.target.innerHTML
            }
        })

        // on hover over a timestamp, will darken it
        document.getElementById("timestampList").addEventListener("mouseover", function(e) {
            if (e.target.tagName === "TD") {
                e.target.style.backgroundColor = "grey"
            }
        })

        // on hover out of a timestamp, will unhighlight it
        document.getElementById("timestampList").addEventListener("mouseout", function(e) {
            if (e.target.tagName === "TD") {
                e.target.style.backgroundColor = ""
            }
        })

        // custom context menu for the timestamp table
        document.getElementById("timestampList").addEventListener("contextmenu", (e) => {
            e.preventDefault()
            // clear the context menu
            contextMenu.innerHTML = ""
            const { clientX: mouseX, clientY: mouseY } = e;
            // create button the set the item clicked to the video time
            var setButton = document.createElement("button")
            setButton.innerHTML = "Set"
            setButton.addEventListener("click", function(a) {
                // get the table timestamp and set it to the current video time
                var timestamp = e.target
                var video = document.getElementById("videoPlayer")
                timestamp.innerHTML = video.currentTime
                setTimestamps()
            })
            // create the delete button
            var deleteButton = document.createElement("button")
            deleteButton.innerHTML = "Delete"
            deleteButton.addEventListener("click", function(a) {
                // get the item and set it to ""
                var item = e.target
                item.innerHTML = ""
                // if both onset and offset are empty, delete the row
                if (item.parentNode.cells[0].innerHTML === "" && item.parentNode.cells[1].innerHTML === "") {
                    item.parentNode.parentNode.removeChild(item.parentNode)
                    IS_ONSET = true
                }
                IS_ONSET = false
                setTimestamps()
            })

            contextMenu.style.top = `${mouseY}px`;
            contextMenu.style.left = `${mouseX}px`;
            contextMenu.style.display = "block";
            contextMenu.classList.add("visible");
            contextMenu.appendChild(setButton)
            contextMenu.appendChild(deleteButton)

        })
        
        // remove the context menu when clicked outside of it
        document.addEventListener("click", function(e) {
            var contextMenu = document.getElementById("context-menu")
            if (contextMenu != null && e.target != contextMenu && contextMenu.classList.contains("visible")) {
                contextMenu.classList.remove("visible")
                contextMenu.innerHTML = ""
            }
        })
        
        // custom context menu for the video list
        document.getElementById("videoList").addEventListener("contextmenu", (e) => {
            e.preventDefault()
            // clear the context menu
            contextMenu.innerHTML = ""
            const { clientX: mouseX, clientY: mouseY } = e;
            // create button to mark the video as complete
            var completeButton = document.createElement("button")
            completeButton.innerHTML = "Mark as Complete"
            completeButton.addEventListener("click", function(a) {
                // get the video row
                var videoRow = e.target.parentNode
                // set the complete column to true
                videoRow.cells[1].innerHTML = "true"
            })
            // add the button to the context menu
            contextMenu.style.top = `${mouseY}px`;
            contextMenu.style.left = `${mouseX}px`;
            contextMenu.style.display = "block";
            contextMenu.classList.add("visible");
            contextMenu.appendChild(completeButton)

        })

        // event listener to update title when video source changes
        document.getElementById("videoPlayer").addEventListener("loadstart", function() {
            document.getElementById("playerTitle").innerHTML = CURRENT_VIDEO_ID
        })

        // an event listener for the search bar
        document.getElementById("search").addEventListener("keyup", function() {
            var input, filter, table, tr, td, i, txtValue;
            input = document.getElementById("search");
            filter = input.value.toUpperCase();
            table = document.getElementById("videoList");
            tr = table.getElementsByTagName("tr");
            for (i = 0; i < tr.length; i++) {
                td = tr[i].getElementsByTagName("td")
                for (j = 0; j < td.length; j++) {
                    txtValue = td[j].textContent || td[j].innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                        break;
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
        })
        
        // warning for closing the window as timestamps must be saved
        //window.onbeforeunload = function() {
        //    return "Are you sure you want to leave?"
        //}
        
        getKeybindings()
        getVideoList()
        const triggerTabList = document.querySelectorAll('#myTab button')
        triggerTabList.forEach(triggerEl => {
            const tabTrigger = new bootstrap.Tab(triggerEl)
        
            triggerEl.addEventListener('click', event => {
            event.preventDefault()
            tabTrigger.show()
            })
        })
    } else {
        // if the user is not logged in, show the login button
        document.getElementById('loginButton').style.display = 'block'
    }
}
xhr.send()