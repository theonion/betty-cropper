function showMessage(message, messageClass) {
    message = message || "An unknown error occurred";
    messageClass = messageClass || "danger";
    var error = $('<div class="alert alert-' + messageClass + '">' + message + '</div>');
    var x = $('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>');
    error.append(x);

    $(".modal-body").prepend(error);
    error.slideDown();
    var errorTimeout = window.setTimeout(function(){
        error.slideUp(function(){$(this).remove();})
    }, 5000);

    x.click(function(){
        window.clearTimeout(errorTimeout);
        error.slideUp(function(){$(this).remove();})
    });
    console.log(message);
}

function processFile(file){
    var previewEl = $(".preview")[0];
    previewEl.onload = function(e){
        $(".upload-form").hide();
        $(".image-form").show();

        if(this.width < 1000) {
            showMessage("<strong>Small Image!</strong> This image is pretty small, and may look pixelated.");
        }

        var name = file.name.split(".")[0];

        $(".name-input").val(name);
        $(".upload-button").removeAttr("disabled");
    }
    previewEl.onerror = function(){
        console.log("Error!");
        $(".image-form").hide();
        $(".upload-form").show();

        showMessage("<strong>Whoops!</strong> It looks like that isn't a valid image.");
    }
    var reader = new FileReader();
    reader.onload = function(e){
        previewEl.src = e.target.result;
    };
    reader.readAsDataURL(file);
}


function initUploadModal(el){
    $("#upload-image").submit(function(e){
        e.preventDefault();

        var name = $("#upload-image .name input").val();
        var credit = $("#upload-image .credit input").val();
        if(name == "") {
            $("#upload-image .name").addClass("has-error");
        }

        var data = new FormData();
        var file = $(".image-picker")[0].files[0];
        data.append("image", file);
        data.append("name", name);
        if (credit !== "") {
            data.append("credit", credit);
        }
        $.ajax({
            url: this.action,
            type: "POST",
            data: data,
            processData: false,
            contentType: false,
            success: function(data, textStatus, xhr){
                $("#upload-modal").modal("hide");
            }
        });
    });
    $(".upload-well").click(function(){
        $(".image-picker").click();
    });
    $(".image-picker").change(function(){
        if (this.files.length == 1) {
            var file = this.files[0];
            processFile(file);
        }
    });
}

function clearUploadModal(el) {
    $(el).find(".image-form").hide();
    $(el).find(".upload-form").show();

    var previewEl = $(".preview")[0];
    previewEl.src = null;
}