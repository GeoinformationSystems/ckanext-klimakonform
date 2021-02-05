/* Module for handling the spatial querying
 */
this.ckan.module('spatial-query', function ($, _) {

    return {
        options: {
            i18n: {
            },
            style: {
                color: '#F06F64',
                weight: 2,
                opacity: 1,
                fillColor: '#F06F64',
                fillOpacity: 0.1,
                clickable: false
            },
            default_extent: [[90, 180], [-90, -180]]
        },
        template: {
            buttons: [
                '<div id="dataset-map-edit-buttons">',
                '<a href="javascript:;" class="btn cancel">Cancel</a> ',
                '<a href="javascript:;" class="btn apply disabled">Apply</a>',
                '</div>'
            ].join('')
        },

        initialize: function () {
            var module = this;
            $.proxyAll(this, /_on/);

            var user_default_extent = this.el.data('default_extent');
            if (user_default_extent) {
                if (user_default_extent instanceof Array) {
                    // Assume it's a pair of coords like [[90, 180], [-90, -180]]
                    this.options.default_extent = user_default_extent;
                } else if (user_default_extent instanceof Object) {
                    // Assume it's a GeoJSON bbox
                    this.options.default_extent = new L.GeoJSON(user_default_extent).getBounds();
                }
            }
            this.el.ready(this._onReady);
        },

        _getParameterByName: function (name) {
            var match = RegExp('[?&]' + name + '=([^&]*)')
                .exec(window.location.search);
            return match ?
                decodeURIComponent(match[1].replace(/\+/g, ' '))
                : null;
        },

        _drawExtentFromCoords: function (xmin, ymin, xmax, ymax) {
            if ($.isArray(xmin)) {
                var coords = xmin;
                xmin = coords[0]; ymin = coords[1]; xmax = coords[2]; ymax = coords[3];
            }
            return new L.Rectangle([[ymin, xmin], [ymax, xmax]],
                this.options.style);
        },

        _drawExtentFromGeoJSON: function (geom) {
            return new L.GeoJSON(geom, { style: this.options.style });
        },

        _onReady: function () {
            var module = this;
            var map;
            var extentLayer;
            var previous_box;
            var previous_extent;
            var is_expanded = false;
            var should_zoom = true;
            var form = $("#dataset-search");
            // CKAN 2.1
            if (!form.length) {
                form = $(".search-form");
            }

            var buttons;

            // Add necessary fields to the search form if not already created
            $(['ext_bbox', 'ext_prev_extent']).each(function (index, item) {
                if ($("#" + item).length === 0) {
                    $('<input type="hidden" />').attr({ 'id': item, 'name': item }).appendTo(form);
                }
            });

            // OK map time
            map = ckan.commonLeafletMap(
                'geokur-map-container',
                this.options.map_config,
                {
                    attributionControl: false,
                    drawControlTooltips: false
                }
            );


            // Initialize the draw control
            map.addControl(new L.Control.Draw({
                position: 'topright',
                draw: {
                    polyline: false,
                    polygon: false,
                    circle: false,
                    marker: false,
                    rectangle: { shapeOptions: module.options.style }
                }
            }));



            // Setup the expanded buttons

            // Handle the cancel expanded action
            $("#btn-map-cancel").on('click', function () {
                if (extentLayer) {
                    map.removeLayer(extentLayer);
                }
                resetMap();
            });

            // Handle the apply expanded action
            $("#btn-map-apply").on('click', function () {
                if (extentLayer) {
                    resetMap();
                    // Eugh, hacky hack.
                    setTimeout(function () {
                        map.fitBounds(extentLayer.getBounds());
                        submitForm();
                    }, 200);
                }
            });

            // When user finishes drawing the box, record it and add it to the map
            map.on('draw:created', function (e) {
                if (extentLayer) {
                    map.removeLayer(extentLayer);
                }
                extentLayer = e.layer;
                $('#ext_bbox').val(extentLayer.getBounds().toBBoxString());
                map.addLayer(extentLayer);
            });

            // Record the current map view so we can replicate it after submitting
            map.on('moveend', function (e) {
                $('#ext_prev_extent').val(map.getBounds().toBBoxString());
            });

            // Ok setup the default state for the map
            map.setView([23, 0], 3);

            // OK, when we expand we shouldn't zoom then
            map.on('zoomstart', function (e) {
                should_zoom = false;
            });



            // Reset map view
            function resetMap() {
                L.Util.requestAnimFrame(map.invalidateSize, map, !1, map._container);
            }

            // Add the loading class and submit the form
            function submitForm() {
                setTimeout(function () {
                    form.submit();
                }, 800);
            }
        }
    }
});
