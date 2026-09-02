#' Retrieve image from BNF
#'
#' Drop-in replacement for bnfimage::bi_image with current Gallica HTTP
#' robustness: quota-aware pacing is delegated to bi_GET_lim(), 429 exhaustion
#' is explicit, and all other HTTP errors are surfaced before image decoding.
#'
#' @export
bi_image = function(identifier = NULL, region = c(0L, 0L, 500L, 500L),
                    size = "full", rotation = 0,
                    quality = c("native", "color", "gray", "bitonal"),
                    format = c("jpg", "tif", "png", "gif", "jp2", "pdf")) {

  if (is_null_or_na(identifier)) {
    stop("Define an identifier for your image")
  }

  bi_check_identifier(identifier)

  if (is.numeric(region) & length(region) == 4) {
    region = paste(region, collapse = ",")
  } else if ((is.numeric(region) & length(region) != 4) |
             (is.character(region) &
              (region[1] != "full" | length(region) != 1))) {
    stop("region has to be a length 4 integer vector or 'full'")
  }

  if (is.numeric(size) & length(size) != 2) {
    stop("size has to be either 'full' or a numeric vector of length 2")
  } else if (is.numeric(size)) {
    size = paste(size, collapse = ",")
  } else if (size != "full" & !is.numeric(size)) {
    stop("size has to be either 'full' or a numeric vector of length 2")
  }

  if (!is.numeric(rotation) | (is.numeric(rotation) & length(rotation) != 1)) {
    stop("rotation has to be a numeric vector of length 1")
  }

  quality = match.arg(quality)
  format = match.arg(format)

  bi_query = bi_GET_lim(identifier, region, size, rotation,
                        paste0(quality, ".", format))

  if (bi_query$status_code == 429) {
    stop("Gallica rate limit still exceeded after retries (HTTP 429)", call. = FALSE)
  } else if (bi_query$status_code == 503) {
    stop("The API could not be reached, please try again later", call. = FALSE)
  } else if (bi_query$status_code == 500) {
    stop("The query gave no answer. Please try another query", call. = FALSE)
  } else if (bi_query$status_code >= 400) {
    httr::stop_for_status(bi_query)
  }

  magick::image_read(bi_query$content)
}
