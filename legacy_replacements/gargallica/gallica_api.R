# Network helper for gargallica.
# Keeps the historical analysis script readable while centralising HTTPS,
# pacing and HTTP 429 / transient error handling.

.gargallica_state <- new.env(parent = emptyenv())
.gargallica_state$last_text_request <- NULL

.gargallica_retry_after <- function(response, attempt) {
  header <- httr::headers(response)[["retry-after"]]
  seconds <- suppressWarnings(as.numeric(header))
  if (is.null(header) || length(seconds) == 0 || is.na(seconds) || seconds < 0) {
    seconds <- min(60, 2 ^ (attempt - 1) * 2)
  }
  seconds
}

.gargallica_wait_text <- function() {
  now <- as.numeric(Sys.time())
  previous <- .gargallica_state$last_text_request
  # Conservative interval below the currently documented 5 requests/minute.
  if (!is.null(previous)) {
    remaining <- 12.5 - (now - previous)
    if (remaining > 0) Sys.sleep(remaining)
  }
  .gargallica_state$last_text_request <- as.numeric(Sys.time())
  invisible(NULL)
}

gargallica_get <- function(url, rate_class = c("default", "texteBrut"), max_retries = 4) {
  rate_class <- match.arg(rate_class)
  attempt <- 1

  repeat {
    if (rate_class == "texteBrut") .gargallica_wait_text()

    response <- httr::GET(
      url,
      httr::add_headers("user-agent" = "gargallica/modernized api.bnf.fr compatibility"),
      httr::timeout(60)
    )

    if (!(response$status_code %in% c(429, 500, 502, 503, 504)) || attempt > max_retries) {
      if (response$status_code >= 400) httr::stop_for_status(response)
      return(response)
    }

    Sys.sleep(.gargallica_retry_after(response, attempt))
    attempt <- attempt + 1
  }
}

gargallica_read_xml <- function(url) {
  response <- gargallica_get(url, rate_class = "default")
  xml2::read_xml(httr::content(response, as = "raw"))
}

gargallica_read_html <- function(url) {
  response <- gargallica_get(url, rate_class = "texteBrut")
  xml2::read_html(httr::content(response, as = "raw"))
}
