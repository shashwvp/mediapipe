const fileInput = document.getElementById("videoFile");
fileInput.addEventListener('change', (event) => {
  const files = event.target.files; // Access the FileList object
  if (files.length > 0) {
    console.log("Selected file:", files[0].name);
  }
});