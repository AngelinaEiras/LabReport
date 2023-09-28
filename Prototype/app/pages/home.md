<!-- home.md -->


<p>
<div>
<script>
date = new Date().toLocaleDateString();
document.write(date);
</script>
</div>

Created at July of 2023
</p>

<h1>Welcome to LabReport Demo</h1>

This tool aims to facilitate communication among scientists and enhance the visualization of conducted experiments and their obtained results.





<!-- ## Upload File

<div id="drop-area">
  <form class="file-form">
    <input type="file" id="fileElem" multiple accept=".txt, .csv" onchange="handleFiles(this.files)">
    <label class="file-label" for="fileElem">Drag and drop a file here or click to browse</label>
  </form>
</div>

<script>
    function handleFiles(files) {
      // Create a FormData object
      const formData = new FormData();
  
      // Append the files to the FormData object
      for (let i = 0; i < files.length; i++) {
        formData.append("file", files[i]);
      }
  
      // Make a POST request to your FastAPI endpoint to handle the uploaded files
      fetch("/process-files", {
        method: "POST",
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        // Handle the response from the server
        console.log(data);
        // Perform any desired actions based on the response
      })
      .catch(error => {
        // Handle any errors that occurred during the request
        console.error(error);
      });
    }
  </script> -->
