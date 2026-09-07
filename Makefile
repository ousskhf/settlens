DATA_RELEASE_URL := https://github.com/ousskhf/settlens/releases/download/data-v1/data-v1.tar.gz
DATA_DIR := data/raw
DATA_ARCHIVE := $(DATA_DIR)/data-v1.tar.gz

.PHONY: download-data
download-data:
	@if ls $(DATA_DIR)/*.parquet >/dev/null 2>&1; then \
		echo "Data already present in $(DATA_DIR) — skipping download. Run 'make clean-data download-data' to refresh."; \
	else \
		mkdir -p $(DATA_DIR); \
		echo "Downloading dataset from $(DATA_RELEASE_URL)..."; \
		curl -fSL --retry 3 -o $(DATA_ARCHIVE) $(DATA_RELEASE_URL) || \
			{ echo "ERROR: could not download dataset from $(DATA_RELEASE_URL)" >&2; exit 1; }; \
		tar -xzf $(DATA_ARCHIVE) -C $(DATA_DIR); \
		rm -f $(DATA_ARCHIVE); \
		echo "Extracted tables into $(DATA_DIR)"; \
	fi

.PHONY: clean-data
clean-data:
	rm -rf $(DATA_DIR)
