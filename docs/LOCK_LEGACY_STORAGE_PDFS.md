# Hashing the original B01-B10 private Supabase PDFs

The private \`papers\` bucket already contains the original B01-B10 files. The available Supabase connector can inspect \`public.papers\` and \`storage.objects\` metadata, but cannot return the private object bytes. The read-only helper below downloads the exact objects locally using a service-role key held only in the user's local environment; it never uploads or changes anything.

## Run locally

1. Clone this private repository and install the backend requirements (PyMuPDF and httpx).
2. Export the existing Supabase project URL and service-role key locally. Do **not** paste the key into ChatGPT, commit it, or put it in a command-line argument.

   \`\`\`bash
   export SUPABASE_URL="https://<your-project-ref>.supabase.co"
   read -s SUPABASE_SERVICE_ROLE_KEY
   export SUPABASE_SERVICE_ROLE_KEY
   \`\`\`

3. Run:

   \`\`\`bash
   python -m benchmark.lock_legacy_storage_pdfs \\
     --out /private/path/B01-B10-binary-lock.json
   \`\`\`

4. Attach only the generated JSON output to the project conversation. Do not attach the service-role key. The JSON contains each paper's SHA-256, byte length and PyMuPDF page count, but no PDF bytes, storage path, user ID or secret.

## Safety properties

- Uses GET requests only against the existing \`papers\` metadata and private Storage object endpoints.
- Requires exactly one completed paper record for each expected filename.
- Verifies exact byte length, PDF header, PyMuPDF readability and page count against the previously observed inventory.
- Does not trust opaque Storage ETags as MD5/SHA-256.
- Does not write to Supabase, mutate Storage, or print credentials.
- Output is marked \`BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT\`; it is not a Git lock until committed to the handoff branch. After the manifest commit, record that exact commit SHA in a follow-up commit before creating any new release-eligible candidate.

Synthetic tests use generated PDFs and fake HTTP responses only; they do not access Supabase.
