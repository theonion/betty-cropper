$(document).ready(function(){
    $('#upload-modal').on("loaded.bs.modal", function(e){
        initUploadModal(this);
    });
    $('#upload-modal').on("hidden.bs.modal", function(e){
        clearUploadModal(this);
    });
});