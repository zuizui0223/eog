#!/usr/bin/env Rscript
# Exact source-authenticated matrix-construction audit, not an occupancy fit.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=4L) {
  stop("usage: Rscript wetland_nmixmatrix_stage_v1.R surveys.csv replay_dir nmixmatrix.R output_dir")
}
survey_path <- args[1]
replay_dir <- args[2]
nmix_path <- args[3]
outdir <- args[4]
dir.create(outdir,showWarnings=FALSE,recursive=TRUE)
source(nmix_path,local=FALSE)
if (!is.function(nmixmatrix)) stop("expected original nmixmatrix function")

native <- read.csv(survey_path,check.names=TRUE,stringsAsFactors=FALSE)
if (nrow(native)!=381L) stop("raw source rows drifted")
species <- c("Pelobates.fuscus","Rana.dalmatina","Bombina.bombina",
             "Hyla.arborea","Pelophylax.ridibundus","Lissotriton.vulgaris",
             "Triturus.dobrogicus","Bufotes.viridis","Bufo.bufo")
if (!all(species %in% names(native))) stop("species header drift")

for (cohort in c("published_q1","published_q2")) {
  mapfile <- file.path(replay_dir,paste0(cohort,"_source_row_mapping.csv"))
  m <- read.csv(mapfile,stringsAsFactors=FALSE,check.names=FALSE)
  if (nrow(m)!=(if (cohort=="published_q1") 540L else 260L)) {
    stop("expected sampled position count drift")
  }
  if (any(is.na(m$eog_native_row_index)) ||
      any(m$eog_native_row_index<1L) ||
      any(m$eog_native_row_index>nrow(native))) stop("invalid source row index")
  selected <- native[m$eog_native_row_index,,drop=FALSE]
  selected$n <- as.integer(m$eog_replay_repeat_index)
  if (!all(selected$site==m$site) ||
      !all(selected$surv==m$surv) ||
      !all(selected$date==m$date) ||
      !all(selected$method==m$method)) stop("native row-map identity mismatch")
  if (!all(selected$n %in% 1:20)) stop("invalid pseudo-repeat positions")

  chunks <- list()
  for (sp in species) {
    # The original R scripts call nmixmatrix(var.name,"site","n",surv)
    # after survreps and per-site repeat-index numbering.
    y <- nmixmatrix(sp,"site","n",selected)
    if (!all(sort(unique(selected$site))==sort(rownames(y))) ||
        ncol(y)!=20L) stop("unexpected site or repeat dimension")
    indices <- cbind(match(selected$site,rownames(y)),
                     match(paste(sp,selected$n,sep="_"),colnames(y)))
    if (any(is.na(indices))) stop("nmixmatrix site/repeat index drift")
    y_value <- as.integer(y[indices])
    raw_count <- as.integer(selected[[sp]])
    if (!identical(y_value,raw_count)) {
      stop(paste("matrix entry differs from selected native record for",sp))
    }
    chunks[[sp]] <- data.frame(
      cohort=cohort,
      site=selected$site,
      repeat_index=selected$n,
      species=gsub("."," ",sp,fixed=TRUE),
      source_row_id=as.integer(m$eog_native_row_index),
      surv=selected$surv,
      method=selected$method,
      date=selected$date,
      native_count=raw_count,
      nmix_count=y_value,
      nmix_detected=as.integer(y_value>0L),
      stringsAsFactors=FALSE
    )
  }
  cells <- do.call(rbind,chunks)
  outfile <- file.path(outdir,paste0(cohort,"_nmixmatrix_cells.csv"))
  write.csv(cells,outfile,row.names=FALSE,fileEncoding="UTF-8")
  cat(paste0("WETLAND_NMIX_STAGE=",cohort,
             " cells=",nrow(cells),
             " positive=",sum(cells$nmix_detected),
             " counts_above_one=",sum(cells$nmix_count>1L),"\n"))
}
