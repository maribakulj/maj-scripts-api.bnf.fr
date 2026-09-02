# HTTP utilities for bnfimage, updated for current public Gallica constraints.

.bi_rate_state <- new.env(parent = emptyenv())
.bi_rate_state$last_request <- list()

bi_base = function() {
  "https://gallica.bnf.fr/iiif"
}

bi_ua = function() {
  paste0("https://github.com/Rekyt/bnfimage R package bnfimage/v.",
         utils::packageVersion("bnfimage"))
}

bi_GET = function(...) {
  httr::GET(
    url = paste(bi_base(), ..., collapse = "/", sep = "/"),
    httr::add_headers("user-agent" = bi_ua()),
    httr::timeout(60)
  )
}

bi_is_hd_request = function(region, size) {
  if (!identical(region, "full")) {
    return(FALSE)
  }
  if (identical(size, "full")) {
    return(TRUE)
  }
  if (is.numeric(size)) {
    return(any(size > 1000, na.rm = TRUE))
  }
  if (is.character(size) && length(size) == 1) {
    first <- suppressWarnings(as.numeric(strsplit(size, ",", fixed = TRUE)[[1]][1]))
    return(!is.na(first) && first > 1000)
  }
  FALSE
}

bi_wait_rate = function(bucket, interval_seconds) {
  now <- as.numeric(Sys.time())
  previous <- .bi_rate_state$last_request[[bucket]]
  if (!is.null(previous)) {
    remaining <- interval_seconds - (now - previous)
    if (remaining > 0) {
      Sys.sleep(remaining)
    }
  }
  .bi_rate_state$last_request[[bucket]] <- as.numeric(Sys.time())
  invisible(NULL)
}

bi_retry_after = function(response, attempt) {
  header <- httr::headers(response)[["retry-after"]]
  seconds <- suppressWarnings(as.numeric(header))
  if (is.null(header) || length(seconds) == 0 || is.na(seconds) || seconds < 0) {
    seconds <- min(60, 2 ^ (attempt - 1) * 2)
  }
  seconds
}

# Compatibility entry point used by bi_image(). High-resolution requests use a
# conservative 12.5 s interval (< 5 requests/minute), while other requests keep
# the historical 3 s pacing. HTTP 429 is retried using Retry-After when present.
bi_GET_lim = function(..., max_retries = 3) {
  parts <- list(...)
  region <- if (length(parts) >= 2) parts[[2]] else NULL
  size <- if (length(parts) >= 3) parts[[3]] else NULL
  high_resolution <- bi_is_hd_request(region, size)
  bucket <- if (high_resolution) "iiif_hd" else "iiif_other"
  interval <- if (high_resolution) 12.5 else 3

  attempt <- 1
  repeat {
    bi_wait_rate(bucket, interval)
    response <- bi_GET(...)
    if (response$status_code != 429 || attempt > max_retries) {
      return(response)
    }
    Sys.sleep(bi_retry_after(response, attempt))
    attempt <- attempt + 1
  }
}

bi_check_identifier = function(id) {
  if (!grepl("^ark:/12148/[\\w/]+$", toString(id), perl = TRUE)) {
    stop("identifier is not valid", call. = FALSE)
  }
}

is_null_or_na = function(x) {
  if (is.null(x)) {
    TRUE
  } else if (is.na(x)) {
    TRUE
  } else {
    FALSE
  }
}
