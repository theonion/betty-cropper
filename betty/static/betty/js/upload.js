function upload() {
    return false;
}

function processFile(file){
    var previewEl = $(".preview")[0];
    previewEl.onload = function(){
        $(".upload-form").hide();
        $(".image-form").show();

        var name = file.name.split(".")[0];

        $(".name-input").val(name);
        $(".upload-button").removeAttr("disabled");
    }
    previewEl.onerror = function(){
        console.log("Error!");
        $(".image-form").hide();
        $(".upload-form").show();

        var error = $('<div class="alert alert-danger alert-bad-image"><strong>Whoops!</strong> It looks like that isn\'t a valid image.</div>');
        error.slideDown();
        $(".upload-form").prepend(error);
        error.fadeIn();
        window.setTimeout(function(){
            error.slideUp(function(){$(this).remove();})
        }, 3000);
    }
    var reader = new FileReader();
    reader.onload = function(e){
        previewEl.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function initUploadModal(el){
    $(".upload-form").onsubmit = upload;
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