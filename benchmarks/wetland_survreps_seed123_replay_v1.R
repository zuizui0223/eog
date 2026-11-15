#!/usr/bin/env Rscript
# Source-authenticated replay of ONLY the original R sampling stage.
# Do NOT execute the published occupancy models or infer field independence.
argv <- commandArgs(trailingOnly = TRUE)
if (length(argv) != 4L) {
  stop("Usage: Rscript wetland_survreps_seed123_replay_v1.R surveys.csv sites.csv survreps.R output_dir")
}
survey_path <- argv[1L]
site_path <- argv[2L]
upstream_function_path <- argv[3L]
outdir <- argv[4L]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

# The source is independently authenticated by SHA256 and Git blob before execution.
source(upstream_function_path, local = FALSE)
if (!is.function(survreps)) stop("Expected pinned survreps function not found")

# The published original scripts use set.seed(123) and leave standard RNGkind.
# Declare sample.kind for this experimental R 4.4.3 replay; historical R version unknown.
RNGkind(kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")

raw <- read.csv(survey_path, check.names = TRUE, stringsAsFactors = FALSE)
sites <- read.csv(site_path, check.names = TRUE, stringsAsFactors = FALSE)
stopifnot(nrow(raw) == 381L, nrow(sites) == 29L)
stopifnot(all(c("site", "surv", "date", "method") %in% names(raw)))
stopifnot(all(c("site", "ci") %in% names(sites)))
raw$eog_native_row_index <- seq_len(nrow(raw))

for (cohort in c("published_q1", "published_q2")) {
  df <- raw
  if (cohort == "published_q1") {
    # Exact exclusions are from published Q1 R script lines 23-27.
    rem <- c("kis-banyato", "vadasz-turjan")
    df <- df[!df$site %in% rem, ]
    expected_sites <- 27L
    expected_rows <- 351L
  } else {
    # Exact filter is from published Q2 R script lines 23-27.
    keep <- unique(sites$site[sites$ci == "intervention"])
    df <- df[df$site %in% keep, ]
    expected_sites <- 13L
    expected_rows <- 188L
  }
  stopifnot(nrow(df) == expected_rows)
  stopifnot(length(unique(df$site)) == expected_sites)

  # Following native preparation from the MD5-verified published Q1/Q2 R code.
  # Addition of eog_native_row_index is audit-only and does not consume RNG.
  df$season <- 1L
  df$X0 <- 1L
  reps <- 20L

  # Each original R script starts with set.seed(123) before any sampling.
  set.seed(123L)
  selected <- survreps(df, "X0", "season", "site", reps)
  stopifnot(nrow(selected) == expected_sites * reps)
  stopifnot(all(table(selected$site) == reps))
  stopifnot(all(selected$X0 == 1L))
  stopifnot(all(selected$eog_native_row_index %in% df$eog_native_row_index))

  # survreps groups output rows consecutively by site in first-seen source order.
  selected$eog_replay_repeat_index <- rep(seq_len(reps), expected_sites)
  chunks <- split(seq_len(nrow(selected)), selected$site)
  stopifnot(all(vapply(chunks, function(ix)
    identical(as.integer(selected$eog_replay_repeat_index[ix]), seq_len(reps)),
    logical(1L))))

  mapping <- selected[, c(
    "site", "surv", "date", "method", "eog_native_row_index",
    "eog_replay_repeat_index"
  )]
  out_path <- file.path(outdir, paste0(cohort, "_source_row_mapping.csv"))
  write.csv(mapping, out_path, row.names = FALSE, fileEncoding = "UTF-8")

  metadata <- c(
    paste0("cohort=", cohort),
    "seed=123",
    "reps=20",
    paste0("R_version=", R.version.string),
    paste0("RNGkind=", paste(RNGkind(), collapse = ";")),
    paste0("input_rows=", nrow(df)),
    paste0("output_rows=", nrow(selected)),
    paste0("source_rows_used_at_least_once=", length(unique(selected$eog_native_row_index)))
  )
  writeLines(metadata, file.path(outdir, paste0(cohort, "_runtime.txt")))
  cat(paste0("EOG_NATIVE_R_SEED123_MAPPING=", cohort, " ",
             length(unique(selected$eog_native_row_index)), "/", nrow(selected)), "\n")
}
