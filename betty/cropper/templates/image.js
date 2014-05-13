(function( w ){
    /* We can request an image at every possible width, but let's limit it to a reasonable number
       We can set these so they correspond to our more common sizes.
    */
    
    var RATIOS = {{ BETTY_RATIOS|safe }};
    var ASPECT_RATIO_TOLERANCE = .1; // 10% tolerance. 
    var breakpoints = [{{ BETTY_WIDTHS|join:","}}];
    function tmpl(text, dict) {
        for (var k in dict) {
            text = text.replace("{" + k + "}", dict[k]);
        }
        return text;
    }
    w.picturefill = function(elements) {
        //don't need to do them all at once. can decide to do lazy load if needed
        if (elements instanceof Array) {
            var ps = elements;
        }
        else if (elements instanceof HTMLElement) {
            var ps = [ elements ];
        }
        else {
            var ps = w.document.getElementsByTagName( "div" );
        }
        var imageData = [];
        for( var i = 0, il = ps.length; i < il; i++ ){
            var el = ps[i];
            if(el.getAttribute( "data-type" ) !== "image" ){
                continue;
            }
            var div = el.getElementsByTagName( "div" )[0];
            if( el.getAttribute( "data-image-id" ) !== null ){
                var id = el.getAttribute( "data-image-id" ),
                    crop = el.getAttribute( "data-crop" );
                var _w = div.offsetWidth,
                    _h = div.offsetHeight;
                
                if (!crop || crop === "" || crop === "auto") {
                    crop = computeAspectRatio(_w, _h);
                }
                if (el.getAttribute("data-format")) {
                    format = el.getAttribute("data-format");
                }
                else {
                    format = "jpg";
                }

                var width = null;
                for (var j = 0; j < breakpoints.length; j++) {
                    if (_w <= breakpoints[j]) {
                        width = breakpoints[j];
                        break;
                    }
                }
                if (width === null) {
                  width = _w;
                }

                // Scale the image up to the pixel ratio
                if (w.devicePixelRatio) {
                  width = Math.round(w.devicePixelRatio * width);
                }

                // Find any existing img element in the picture element
                var picImg = div.getElementsByTagName( "img" )[ 0 ];

                if(!picImg){
                    // for performance reasons this will be added to the dom later
                    picImg = w.document.createElement( "img" );
                    picImg.alt = el.getAttribute( "data-alt" );
                }

                //picImg.className = "loading";
                picImg.onload = function() {
                    //this.className = "";
                };
                // if the existing image is larger (or the same) than the one we're about to load, do not update.
                //however if the crop changes, we need to reload.
                if (width > 0) {

                    //ie8 doesn't support natural width, always load.
                    if (typeof picImg.naturalWidth === "undefined" || picImg.naturalWidth < width ||
                        crop !== computeAspectRatio(picImg.naturalWidth, picImg.naturalHeight)) {
                        var id_str = "";
                        for(var ii=0; ii < id.length; ii++) {
                            if ((ii % 4) === 0) {
                                id_str += "/";
                            }
                            id_str += id.charAt(ii);
                        }
                        var url = "{{ BETTY_IMAGE_URL }}" + "/" + id_str + "/" + crop + "/" + width + "." + format;

                        imageData.push({
                            'div': div,
                            'img': picImg,
                            'url': url
                        });
                    }
                }
            }
        }
        // all DOM updates should probably go here
        for(var i = 0; i < imageData.length; i++) {
            var data = imageData[i];
            data.img.src = data.url;
            if (!data.img.parentNode) {
                data.div.appendChild(data.img);
            }
        }
    };

    function computeAspectRatio(_w, _h) {
        if (_w !== 0 && _h !== 0) {
            var aspectRatio = _w/_h;
            for (var i in RATIOS) {
              if (Math.abs(aspectRatio - RATIOS[i][1]) / RATIOS[i][1] < ASPECT_RATIO_TOLERANCE) {
                return RATIOS[i][0];
              }
            }
        }
        else {
            return "16x9"
        }
    }

    // Run on resize and domready (w.load as a fallback)
    if (!w.IMAGE_LISTENERS_DISABLED) {
        if( w.addEventListener ){
            var pictureFillTimeout;
            w.addEventListener( "resize",
                function() {
                    clearTimeout(pictureFillTimeout);
                    pictureFillTimeout = setTimeout(w.picturefill, 100);
                }, false );

            w.addEventListener( "DOMContentLoaded", function(){
                w.picturefill();
                // Run once only
                w.removeEventListener( "load", w.picturefill, false );
            }, false );
            w.addEventListener( "load", w.picturefill, false );

        }
        else if( w.attachEvent ){
            w.attachEvent( "onload", w.picturefill );
        }
    }
}( this ));