(function(w){
  /* We can request an image at every possible width, but let's limit it to a reasonable number
   We can set these so they correspond to our more common sizes.
   */
  var IMAGE_URL = w.BETTY_IMAGE_URL || "{{ BETTY_IMAGE_URL }}",
      RATIOS = {{ BETTY_RATIOS|safe }},
      ASPECT_RATIO_TOLERANCE = .1, // 10% tolerance.
      MAX_WIDTH = {{ BETTY_MAX_WIDTH }},
      PICTUREFILL_SELECTOR = w.PICTUREFILL_SELECTOR || "div",
      breakpoints = [{{ BETTY_WIDTHS|join:","}}];

  // Credit to https://remysharp.com/2010/07/21/throttling-function-calls
  function throttle(fn, threshhold, scope) {
    threshhold || (threshhold = 250);
    var last,
        deferTimer;
    return function () {
      var context = scope || this;

      var now = +new Date,
          args = arguments;
      if (last && now < last + threshhold) {
        // hold on to it
        clearTimeout(deferTimer);
        deferTimer = setTimeout(function () {
          last = now;
          fn.apply(context, args);
        }, threshhold);
      } else {
        last = now;
        fn.apply(context, args);
      }
    };
  }

  w.picturefill = function picturefill (elements, forceRerender) {
    // It is sometimes desirable to scroll without loading images as we go.
    if (picturefill.paused()) {
      return;
    }
    // get elements to picturefill
    var ps;
    if (elements instanceof Array) {
      ps = elements;
    } else if (elements instanceof HTMLElement) {
      ps = [elements];
    } else {
      ps = w.document.querySelectorAll(PICTUREFILL_SELECTOR);
    }

    // loop through elements and fill them in
    var imageData = [];
    for (var i = 0, il = ps.length; i < il; i++){
      var el = ps[i];

      // ensure this element is actually a image to picturefill
      if(el.getAttribute("data-type") !== "image" ){
        // not image to fill, skip this one
        continue;
      }

      // check if image is in viewport for lazy loading, and
      // preload images if they're within 100px of being shown above scroll,
      // within 250px of being shown below scroll.
      var elementRect = el.getBoundingClientRect(),
          innerHeight = w.innerHeight || w.document.documentElement.clientHeight,
          visible = elementRect.top <= (innerHeight + 250) && elementRect.top >= -100;

      // this is a div to picturefill, start working on it if it hasn't been rendered yet
      if (el.getAttribute("data-image-id") !== null
          && visible 
          && (forceRerender || !el.getAttribute("data-rendered"))) {
        var imageContainer = el.getElementsByTagName("div")[0],
            imageId = el.getAttribute("data-image-id"),
            imageCrop = el.getAttribute("data-crop"),
            format = el.getAttribute("data-format") || "jpg";

        // construct ID path for image
        var idStr = "";
        for(var ii = 0; ii < imageId.length; ii++) {
          if ((ii % 4) === 0) {
            idStr += "/";
          }
          idStr += imageId.charAt(ii);
        }

        // find any existing img element in the picture element
        var picImg = imageContainer.getElementsByTagName("img")[0];
        if(!picImg){
          // for performance reasons this will be added to the dom later
          picImg = w.document.createElement("img");

          var alt = el.getAttribute("data-alt");
          if (alt) {
            picImg.alt = alt;
          }
        }

        // determine what to do based on format
        if (format === "gif") {
          // for GIFs, we just dump out original
          imageData.push({
            'div': imageContainer,
            'img': picImg,
            'url': IMAGE_URL + idStr + "/animated/original.gif"
          });
        } else {
          // determine size & crop for PNGs & JPGs.
          var _w = imageContainer.offsetWidth,
              _h = imageContainer.offsetHeight;

          if (!imageCrop || imageCrop === "") {
            imageCrop = computeAspectRatio(_w, _h);
          }

          // scale up to the pixel ratio if there's some pixel ratio defined
          if (w.devicePixelRatio) {
            _w = Math.round(w.devicePixelRatio * _w);
            _h = Math.round(w.devicePixelRatio * _h);
          }

          // determine if a breakpoint width should be used, otherwise use previously defined width
          var width = null;
          for (var j = 0; j < breakpoints.length; j++) {
            if (_w <= breakpoints[j]) {
              width = breakpoints[j];
              break;
            }
          }
          if (width === null) {
            if (_w > MAX_WIDTH) {
              width = MAX_WIDTH;
            } else {
              width = _w;
            }
          }

          // if the existing image is larger (or the same) than the one we're about to load, do not update.
          //  however if the crop changes, we need to reload.
          if (width > 0) {
            //ie8 doesn't support natural width, always load.
            if (typeof picImg.naturalWidth === "undefined" || picImg.naturalWidth < width
                || imageCrop !== computeAspectRatio(picImg.naturalWidth, picImg.naturalHeight)) {
              // put image in image data to render
              imageData.push({
                'div': imageContainer,
                'img': picImg,
                'url': IMAGE_URL + idStr + "/" + imageCrop + "/" + width + "." + format
              });
            }
          }
        }
      }
    }
    // loop through image data and insert images, all DOM updates should probably go here
    for(var i = 0; i < imageData.length; i++) {
      var data = imageData[i];
      data.img.src = data.url;
      if (!data.img.parentNode) {
        data.div.appendChild(data.img);
        data.div.parentNode.setAttribute("data-rendered", "true");
      }
    }
  };

  /**
   * picturefill pause and resume.
   * Useful to prevent loading unneccessary images, such as when scrolling
   * the reading list.
   */
  var isPaused = false;
  picturefill.pause = function () {
    isPaused = true;
  };

  picturefill.resume = function () {
   isPaused = false;
   picturefill();
  };

  picturefill.paused = function () {
   return isPaused;
  };

  /**
   * Figure out best aspect ratio based on width, height, and given aspect ratios.
   */
  function computeAspectRatio(_w, _h) {
    if (_w !== 0 && _h !== 0) {
      var aspectRatio = _w/_h;
      for (var i in RATIOS) {
        if (Math.abs(aspectRatio - RATIOS[i][1]) / RATIOS[i][1] < ASPECT_RATIO_TOLERANCE) {
          return RATIOS[i][0];
        }
      }
    } else {
      return "16x9";
    }
  }

  function addEventListener(ele, event, callback) {
    if (ele.addEventListener) {
      ele.addEventListener(event, callback, false);
    } else if (ele.attachEvent) {
      ele.attachEvent("on" + event, callback);
    }
  }

  function removeEventListener(ele, event, callback) {
    if (ele.removeEventListener) {
        ele.removeEventListener(event, callback, false);
    } else if (ele.detachEvent) {
        ele.detachEvent("on" + event, callback);
    }
  }

  // Run on resize and domready (w.load as a fallback)
  if (!w.IMAGE_LISTENERS_DISABLED) {

    addEventListener(w, "load", picturefill);
    addEventListener(w, "DOMContentLoaded", function () {
      picturefill();
      removeEventListener(w, "load");
    });

    var resizeTimeout;
    addEventListener(w, "resize", function () {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(function () {
        picturefill(null, true);
      }, 100);
    });

    addEventListener(w, "scroll", throttle(picturefill, 100));

  }

}(this));
