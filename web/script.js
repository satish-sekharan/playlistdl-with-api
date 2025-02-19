console.log("Script loaded"); // Add this line at the beginning of script.js

async function download() {
    const spotifyLink = document.getElementById('spotifyLink').value;

    if (!spotifyLink) {
        document.getElementById('result').innerText = "Please enter a Spotify link.";
        return;
    }

    // Clear previous logs and result
    const logsElement = document.getElementById('logs');
    logsElement.innerHTML = "";
    document.getElementById('result').innerText = "";

    // Show and reset the progress bar
    const progressBar = document.getElementById('progress');
    progressBar.style.display = 'block';
    progressBar.value = 0;
    const increment = 10; // Smaller increment for more gradual progress

    // Create an EventSource to listen to the server-sent events
    const eventSource = new EventSource(`/download?spotify_link=${encodeURIComponent(spotifyLink)}`);

    eventSource.onmessage = function(event) {
        const log = event.data;
        
        if (log.startsWith("DOWNLOAD:")) {
            // Download link received, set progress to 100%
            progressBar.value = 100;

            const path = log.split("DOWNLOAD: ")[1];
            const downloadLink = document.createElement('a');
            downloadLink.href = `/downloads/${path}`;
            downloadLink.download = path.split('/').pop(); // Extract the filename for download
            downloadLink.innerText = "Click to download your file";
            document.getElementById('result').appendChild(downloadLink);
            downloadLink.click();

            // Close the EventSource and hide the progress bar
            eventSource.close();
            progressBar.style.display = 'none';
        } else if (log.includes("Download completed") || log.includes("Download process completed successfully")) {
            // Show a success message in logs
            logsElement.innerHTML += "Download completed successfully.<br>";
        } else if (log.startsWith("Error")) {
            // Display error message and close EventSource
            document.getElementById('result').innerText = `Error: ${log}`;
            eventSource.close();
            progressBar.style.display = 'none';
        } else {
            // Increase progress gradually
            progressBar.value = Math.min(progressBar.value + increment, 95);

            // Append log output to logs section
            logsElement.innerHTML += log + "<br>";
            logsElement.scrollTop = logsElement.scrollHeight;
        }
    };

    eventSource.onerror = function() {
        // Only show error if no success message was received
        if (!logsElement.innerHTML.includes("Download completed successfully")) {
            document.getElementById('result').innerText = "Error occurred while downloading.";
        }
        progressBar.style.display = 'none';
        eventSource.close();
    };
}

const showPirate = () => {
    
}
