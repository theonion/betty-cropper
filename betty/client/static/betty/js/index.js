$(document).ready(function(){
    $('#upload-modal').on("loaded.bs.modal", function(e){
        initUploadModal(this);
    });
    $('#upload-modal').on("hidden.bs.modal", function(e){
        clearUploadModal(this);
    });
});

$(document.body).on('click', '#size-select li', function (event) {
    var $t = $(event.currentTarget),
    	l = $(this).find('a');
    $('#size').val(l.attr('data-title'));
	$t.closest('.input-group-btn')
        .find('[data-bind="label"]').text($t.text())
        .end()
        .children('.dropdown-toggle').dropdown('toggle');
    return false;
});