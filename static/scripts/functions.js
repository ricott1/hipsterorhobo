var canvas, ctx;
var ratio;

$(document).ready(function(e) {
    canvas = document.getElementById("mainCanvas");
    ctx = canvas.getContext("2d");
    var img = new Image;
    img.onload = function() {
        ctx.drawImage(img, 5, 5, canvas.width - 10, canvas.height - 10);
    };
    img.src = 'images/noimage.png';
    ctx.strokeStyle = 'blue';
    ctx.lineWidth = '5';
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
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
                ctx.font = '20pt Arial';
                ctx.beginPath();
                var jsondata = JSON.parse(data);
                for (var key in jsondata) {
                    ctx.lineWidth = 5;
                    var x = jsondata[key]['x'];
                    var y = jsondata[key]['y'];
                    var w = jsondata[key]['w'];
                    var h = jsondata[key]['h'];
                    console.log(x, y);
                    ctx.strokeStyle = "rgb(" + parseInt(0.1 * jsondata[key]['confidence']) + "," + parseInt(Math.max(0, 255 - 2.5 * jsondata[key]['confidence'])) + ",0)";
                    ctx.rect(x, y, w, h);
                    ctx.stroke();

                    ctx.lineWidth = 2;
                    ctx.strokeStyle = 'black';
                    var idtext = ['Hipster', 'Hobo'][jsondata[key]['id'] - 1];
                    ctx.strokeText(idtext + "  " + parseInt(Math.max(0, 100 - jsondata[key]['confidence'])) + "%", x, y+5);
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
                var img = new Image;
                img.onload = function() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0); // Or at whatever offset you like
                };
                img.src = 'images/noimage.png';
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
        var img = new Image;
        var maxWidth = canvas.width; // Max width for the image
        var maxHeight = canvas.height; // Max height for the image
        img.onload = function() {
            var width = img.width; // Current image width
            var height = img.height; // Current image height
            ratio = Math.min((maxWidth / width), (maxHeight / height));
            console.log(width, maxWidth, height, maxHeight, ratio);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            //ctx.drawImage(img, 0, 0, width * ratio, height * ratio);
            ctx.drawImage(img, 0, 0,canvas.width, canvas.height);
        };
        img.src = e.target.result;
    };
});