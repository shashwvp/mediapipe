const fileInput = document.getElementById("videoFile");
fileInput.addEventListener('change', (event) => {
  const files = event.target.files; // Access the FileList object
  if (files.length > 0) {
    console.log("Selected file:", files[0].name);
  }
});

var ctx = document.getElementById("canvas").getContext('2d');
    var img = new Image();
    img.src = "{{ url_for('video_feed') }}";

    // need only for static image
    //img.onload = function(){   
    //    ctx.drawImage(img, 0, 0);
    //};

    // need only for animated image
    function refreshCanvas(){
        ctx.drawImage(img, 0, 0);
    };
    window.setInterval("refreshCanvas()", 50);