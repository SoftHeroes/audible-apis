#!/bin/bash
# Define the locales as an array
IFS=',' read -ra LOCALES <<< "$BATCH_LOCALE"

# Iterate over each locale and run the script
for locale in "${LOCALES[@]}"; do
    python3 save-products-s3.py \
        --region_name="$REGION_NAME" \
        --bucket_name="$BUCKET_NAME" \
        --locale_code="$locale" \
        --base_url="$BASE_URL"
done
