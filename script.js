const videoUploadButton = document.getElementById("submitVideo");

videoUploadButton.addEventListener('click', () => {
  // send to python main file
  var ctx = document.getElementById("canvas").getContext('2d');
  var img = new Image();
  img.src = "{{ url_for('video_feed') }}";

  // need only for animated image
  function refreshCanvas(){
      ctx.drawImage(img, 0, 0);
  };
  window.setInterval("refreshCanvas()", 50);
});

