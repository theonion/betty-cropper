$('#scroll').infinitescroll({
    navSelector     : "#pagination",
    nextSelector    : "a#next",
    itemSelector    : "#scroll li",
    animate         : true,
    donetext        : "End of available images."
},function(){ initPopover(); });

$(document).ready(function(){
    initPopover();

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

function initPopover() {
    $('#results li a').popover({ 
        html : true,
        content: function() { return $(this).next('.details').html(); },
        trigger: 'hover', // Need 2 figure out something to do at mobile bc no hover
        placement: 'auto',
        delay: { show: 500, hide: 100 },
        title: 'Details'
    });
}