# Remplacement P0 du script gargallica/full_hd_image.R.
# Ne dépend que de httr. Respecte par défaut le plafond BnF IIIF HD de 5/minute.

.bnf_hd_state <- new.env(parent = emptyenv())
.bnf_hd_state$last_request <- NULL

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0) y else x

.bnf_hd_wait <- function(min_interval_seconds) {
  now <- as.numeric(Sys.time())
  last <- .bnf_hd_state$last_request
  if (!is.null(last)) {
    wait <- min_interval_seconds - (now - last)
    if (wait > 0) Sys.sleep(wait)
  }
  .bnf_hd_state$last_request <- as.numeric(Sys.time())
}

get_hd_image <- function(ark, output_dir = "img", page = 1, width = "full",
                         min_interval_seconds = 12.25) {
  if (!requireNamespace("httr", quietly = TRUE)) {
    stop("Le package R 'httr' est requis")
  }
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  ark <- sub("^.*ark:/12148/", "", ark)
  ark <- sub("/.*$", "", ark)
  size <- if (identical(width, "full")) "full" else paste0(as.integer(width), ",")
  url <- sprintf(
    "https://gallica.bnf.fr/iiif/ark:/12148/%s/f%d/full/%s/0/native.jpg",
    ark, as.integer(page), size
  )
  .bnf_hd_wait(min_interval_seconds)
  output <- file.path(output_dir, sprintf("%s_f%d.jpg", ark, as.integer(page)))
  response <- httr::GET(
    url,
    httr::user_agent("bnf-api-p0/0.1.3"),
    httr::write_disk(output, overwrite = TRUE)
  )
  if (httr::status_code(response) == 429) {
    retry_after <- httr::headers(response)[["retry-after"]]
    stop(sprintf("Quota BnF atteint (429). Retry-After=%s", retry_after %||% "non fourni"))
  }
  httr::stop_for_status(response)
  output
}
