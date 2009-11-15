OPAQUE = 255
TRANSPARENT = 0


def _build_zoom_mapping(conf=None, MAX_ZOOM=31):
    """Build and return the zoom_to_opacity mapping

    This is a mapping of zoom levels to opacity levels. It is applied in 
    addition to any per-pixel alpha from the color scheme.

    """
    if conf is None:
        from gheat import MAX_ZOOM, conf # won't use these in testing


    # Read and validate configuration.
    # ================================

    zoom_opaque = conf.get('zoom_opaque', '-15')
    try:
        zoom_opaque = int(zoom_opaque)
    except ValueError:
        raise ConfigurationError("zoom_opaque must be an integer.")
    
    zoom_transparent = conf.get('zoom_transparent', '15')
    try:
        zoom_transparent = int(zoom_transparent)
    except ValueError:
        raise ConfigurationError("zoom_transparent must be an integer.")



    # Build the mapping.
    # ==================

    num_opacity_steps = zoom_transparent - zoom_opaque
    zoom_to_opacity = dict()
    if num_opacity_steps < 1:               # don't want general fade
        for zoom in range(0, MAX_ZOOM + 1):
            zoom_to_opacity[zoom] = None 
    else:                                   # want general fade
        opacity_step = OPAQUE / float(num_opacity_steps) # chunk of opacity
        for zoom in range(0, MAX_ZOOM + 1):
            if zoom <= zoom_opaque:
                opacity = OPAQUE 
            elif zoom >= zoom_transparent:
                opacity = TRANSPARENT
            else:
                opacity = int(OPAQUE - ((zoom - zoom_opaque) * opacity_step))
            zoom_to_opacity[zoom] = opacity

    return zoom_to_opacity

zoom_to_opacity = _build_zoom_mapping()

