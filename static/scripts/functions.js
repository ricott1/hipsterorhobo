$(document).ready(function(e) {
    $("#uploadimage").on('submit', (function(e) {
        e.preventDefault();
        $("#message").empty();
        $('#loading').show();
        var fd = new FormData(this);
        $.ajax({
            url: "http://localhost:80", // Url to which the request is send
            type: "POST", // Type of request to be send, called as method
            data: fd, // Data sent to server, a set of key/value pairs (i.e. form fields and values)
            contentType: false, // The content type used when sending data to the server.
            cache: false, // To unable request pages to be cached
            processData: false, // To send DOMDocument or non processed data file it is set to false
            success: function(data) // A function to be called if request succeeds
            {
                $('#loading').hide();
                //$('#image_preview').hide();
                //$("#message").html(JSON.parse(data[0]));

                var canvas = document.getElementById("myCanvas");
                var ctx = canvas.getContext("2d");
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.font = '20pt Arial';
                var img = document.getElementById("previewing");
                var width = $('#previewing').width(); // Current image width
                var height = $('#previewing').height(); // Current image height
                ctx.drawImage(img, x=0, y=0, width=width, height=height);
                ctx.beginPath();

                var jsondata = JSON.parse(data);
                for (var key in jsondata) {
                    console.log(jsondata[key], canvas.width / img.width);

                    ctx.lineWidth = 5;
                    var x = parseInt(jsondata[key]['x'] * width / img.width);
                    var y = jsondata[key]['y'] * width / img.width;
                    var w = jsondata[key]['w'] * width / img.width;
                    var h = jsondata[key]['h'] * width / img.width;
                    ctx.strokeStyle = "rgb(" + parseInt(0.1 * jsondata[key]['confidence']) + "," + parseInt(Math.max(0, 255 - 2.5 * jsondata[key]['confidence'])) + ",0)";
                    ctx.rect(x, y, w, h);
                    ctx.stroke();

                    ctx.lineWidth = 2;
                    ctx.strokeStyle = 'black';
                    var idtext = ['Hipster', 'Hobo'][jsondata[key]['id'] - 1];
                    ctx.strokeText(idtext + "  " + parseInt(Math.max(0, 100 - jsondata[key]['confidence'])) + "%", x + 10, y - 10);
                }

            }
        });
    }));

    // Function to preview image after validation
    $(function() {
        $("#file").change(function() {
            $("#message").empty(); // To remove the previous error message
            var file = this.files[0];
            var imagefile = file.type;
            var match = ["image/jpeg", "image/png", "image/jpg"];
            if (!((imagefile == match[0]) || (imagefile == match[1]) || (imagefile == match[2]))) {
                $('#myCanvas #previewing').attr('src', 'noimage.png');
                $("#message").html("<p id='error'>Please Select A valid Image File</p>" + "<h4>Note</h4>" + "<span id='error_message'>Only jpeg, jpg and png Images type allowed</span>");
                return false;
            } else {
                var reader = new FileReader();
                reader.onload = imageIsLoaded;
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    function imageIsLoaded(e) {
        $("#file").css("color", "green");
        $('#image_preview').css("display", "block");
        $('#previewing').attr('src', e.target.result);

        var maxWidth = $('#image_preview').width(); // Max width for the image
        var maxHeight = $('#image_preview').height(); // Max height for the image

        var width = $('#previewing').width(); // Current image width
        var height = $('#previewing').height(); // Current image height
        var ratio = Math.min(maxWidth / width, maxHeight / height); 
        console.log(width, maxWidth, height, maxHeight, ratio);// Used for aspect ratio
        $('#previewing').width(parseInt(width * ratio)); // Set new width
        $('#previewing').css("height", parseInt(height * ratio)); // Scale height based on ratio


        console.log(width, maxWidth, height, maxHeight, ratio);
    };
});