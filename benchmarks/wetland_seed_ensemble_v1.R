#!/usr/bin/env Rscript
# Post-exposure processing sensitivity: ALL seeds 1..256, no occupancy fits.
# Input argv: SHA-authenticated surveys, sites, pinned survreps R source,
#             existing seed123 mapping directory, output directory.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=5L) stop("usage: Rscript wetland_seed_ensemble_v1.R surveys.csv sites.csv survreps.R replay_dir output_dir")
survey_path <- args[1L]; site_path <- args[2L]
survreps_path <- args[3L]; replay_dir <- args[4L]; outdir <- args[5L]
dir.create(outdir,showWarnings=FALSE,recursive=TRUE)

source(survreps_path,local=FALSE)
if (!is.function(survreps)) stop("authenticated upstream survreps unavailable")
RNGkind(kind="Mersenne-Twister",normal.kind="Inversion",sample.kind="Rejection")
raw <- read.csv(survey_path,stringsAsFactors=FALSE,check.names=TRUE)
sites <- read.csv(site_path,stringsAsFactors=FALSE,check.names=TRUE)
if (nrow(raw)!=381L || nrow(sites)!=29L) stop("archived source dimensions drifted")
raw$eog_native_row_index <- seq_len(nrow(raw))
species <- c(
  "Pelobates.fuscus","Rana.dalmatina","Bombina.bombina",
  "Hyla.arborea","Pelophylax.ridibundus","Lissotriton.vulgaris",
  "Triturus.dobrogicus","Bufotes.viridis","Bufo.bufo"
)
if (!all(species %in% names(raw))) stop("archived nine-species schema drift")

make_cohort <- function(cohort) {
  df <- raw
  if (cohort=="published_q1") {
    rem <- c("kis-banyato","vadasz-turjan")
    df <- df[!df$site %in% rem,,drop=FALSE]
    expected <- c(27L,351L,144L)
  } else if (cohort=="published_q2") {
    keep <- unique(sites$site[sites$ci=="intervention"])
    df <- df[df$site %in% keep,,drop=FALSE]
    expected <- c(13L,188L,77L)
  } else stop("unknown cohort")
  ids <- unique(df$site)
  if (length(ids)!=expected[1] || nrow(df)!=expected[2]) stop("study roster drift")
  df$season <- 1L
  df$X0 <- 1L
  y <- matrix(FALSE,nrow=length(ids),ncol=length(species),
              dimnames=list(ids,gsub("."," ",species,fixed=TRUE)))
  for (site in ids) {
    sub <- df[df$site==site,species,drop=FALSE]
    y[site,] <- colSums(sub>0L)>0
  }
  if (sum(y)!=expected[3]) stop("raw recorded positive site-species drift")
  list(rows=df,sites=ids,original=y)
}
cohorts <- list(
  published_q1=make_cohort("published_q1"),
  published_q2=make_cohort("published_q2")
)

# The previously published seed=123 selection is an independent regression
# receipt produced by a separate R script/workflow before this experiment.
expected_mapping <- lapply(names(cohorts), function(cohort) {
  path <- file.path(replay_dir,paste0(cohort,"_source_row_mapping.csv"))
  if (!file.exists(path)) stop("missing prior seed123 source-row replay for ",cohort)
  mapping <- read.csv(path,stringsAsFactors=FALSE)
  if (!all(c("site","eog_native_row_index") %in% names(mapping))) stop("invalid seed123 map")
  mapping
})
names(expected_mapping) <- names(cohorts)

sample_cohort <- function(seed,cohort) {
  c <- cohorts[[cohort]]
  set.seed(as.integer(seed))
  chosen <- survreps(c$rows,"X0","season","site",20L)
  if (nrow(chosen)!=20L*length(c$sites) ||
      !identical(as.character(unique(chosen$site)),as.character(c$sites)) ||
      !all(as.integer(table(chosen$site))==20L)) {
    stop("authentic sampling stage yielded unexpected site/order/row count")
  }
  if (seed==123L) {
    prior <- expected_mapping[[cohort]]
    if (!identical(as.character(chosen$site),as.character(prior$site)) ||
        !identical(as.integer(chosen$eog_native_row_index),
                   as.integer(prior$eog_native_row_index))) {
      stop("original seed123 mapping regression violated")
    }
  }
  observed <- matrix(FALSE,nrow=length(c$sites),ncol=length(species),
                     dimnames=dimnames(c$original))
  for (site in c$sites) {
    sub <- chosen[chosen$site==site,species,drop=FALSE]
    observed[site,] <- colSums(sub>0L)>0
  }
  if (any(observed & !c$original)) stop("sampling created native-absent site-species positive")
  lost <- c$original & !observed
  native_ids <- as.integer(chosen$eog_native_row_index)
  if (any(is.na(native_ids))) stop("source row ID not preserved")
  detail <- as.data.frame(as.table(c$original),stringsAsFactors=FALSE)
  names(detail) <- c("site","species","native_positive")
  # Species columns are from original native table (dots -> spaces).
  detail <- detail[detail$native_positive, c("site","species"),drop=FALSE]
  detail$seed <- as.integer(seed)
  detail$cohort <- cohort
  detail$retained_after_sampling <- as.integer(
    mapply(function(site,sp) observed[as.character(site),as.character(sp)],
           detail$site,detail$species)
  )
  detail <- detail[,c("cohort","seed","site","species","retained_after_sampling")]
  list(
    observed=observed,
    detail=detail,
    lost=sum(lost),
    distinct_rows=length(unique(native_ids)),
    repeated_positions=nrow(chosen)-length(unique(native_ids))
  )
}

fixed_seeds <- seq.int(1L,256L)
summary_rows <- vector("list",length(fixed_seeds))
details <- vector("list",length(fixed_seeds))
for (i in seq_along(fixed_seeds)) {
  seed <- fixed_seeds[i]
  q1 <- sample_cohort(seed,"published_q1")
  q2 <- sample_cohort(seed,"published_q2")
  common <- cohorts$published_q2$sites
  if (!all(common %in% rownames(q1$observed))) stop("Q2 not nested within Q1")
  disagree <- sum(q1$observed[common,,drop=FALSE] != q2$observed[common,,drop=FALSE])
  q1_shared_lost <- sum(
    (cohorts$published_q1$original & !q1$observed)[common,,drop=FALSE]
  )
  summary_rows[[i]] <- data.frame(
    seed=seed,
    q1_lost_positive_site_species=q1$lost,
    q2_lost_positive_site_species=q2$lost,
    q1_lost_among_shared13=q1_shared_lost,
    overlap_pseudo_detection_disagreements=disagree,
    q1_distinct_original_rows=q1$distinct_rows,
    q2_distinct_original_rows=q2$distinct_rows,
    q1_repeated_row_positions=q1$repeated_positions,
    q2_repeated_row_positions=q2$repeated_positions
  )
  details[[i]] <- rbind(q1$detail,q2$detail)
}
summary_df <- do.call(rbind,summary_rows)
pair_df <- do.call(rbind,details)

key123 <- summary_df[summary_df$seed==123L,,drop=FALSE]
if (nrow(key123)!=1L ||
    key123$q1_lost_positive_site_species != 3L ||
    key123$q2_lost_positive_site_species != 6L ||
    key123$q1_distinct_original_rows != 287L ||
    key123$q2_distinct_original_rows != 153L ||
    key123$overlap_pseudo_detection_disagreements != 7L) {
  stop("original seed123 results do not reproduce")
}
if (nrow(summary_df)!=256L || nrow(pair_df)!=256L*(144L+77L)) stop("fixed seed roster not complete")
if (!identical(sort(unique(summary_df$seed)),as.integer(fixed_seeds))) stop("seed selection changed")
write.csv(summary_df,file.path(outdir,"seed_ensemble_summary.csv"),
          row.names=FALSE,fileEncoding="UTF-8")
write.csv(pair_df,file.path(outdir,"seed_ensemble_native_positive_pairs.csv"),
          row.names=FALSE,fileEncoding="UTF-8")
writeLines(c("R_version=R 4.4.3 (requested by CI)",
             paste0("runtime=",R.version.string),
             paste0("RNGkind=",paste(RNGkind(),collapse=";")),
             "seed_roster=1..256",
             paste0("source_survreps_pinned=",survreps_path),
             "seed123_reproduces_original_source_row_mapping=true"),
           file.path(outdir,"seed_ensemble_runtime.txt"))
cat("WETLAND_SEED_ENSEMBLE_COMPLETE=",
    "Q1_mean_lost=",mean(summary_df$q1_lost_positive_site_species),
    " Q2_mean_lost=",mean(summary_df$q2_lost_positive_site_species),
    " mean_paired_disagreement=",mean(summary_df$overlap_pseudo_detection_disagreements),
    " seed123_overlap_disagreement=",key123$overlap_pseudo_detection_disagreements,
    "\n",sep="")
