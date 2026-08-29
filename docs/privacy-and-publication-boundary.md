# Privacy and Publication Boundary

## Public-safe content

- source code and tests;
- synthetic listing fixtures;
- generic scoring methodology;
- empty templates and schemas;
- deterministic generated outputs from synthetic inputs;
- aggregate engineering lessons that do not identify a person or live property.

## Private content

Keep the following outside version control:

- a real person's name, contact information, immigration or application details;
- real preference weights tied to an identifiable person;
- landlord, broker, leasing-agent or roommate contact records;
- lease drafts, guarantor documents, financial evidence or payment records;
- live availability, private portal data or data whose publication license is unclear;
- local browser state, cookies, credentials and API keys;
- absolute paths that reveal a workstation username.

## Recommended local workflow

```text
repository/
  examples/              synthetic and publishable
private_data/            outside repository or gitignored
  listings.csv
  preferences.json
private_output/          outside repository or gitignored
```

Run the CLI with explicit paths to private inputs and private outputs. Do not copy the resulting report into the public repository.

## De-identification is not enough by itself

Removing a name does not make a search safely public. A combination of exact dates, budget, institution, building, unit, lease term and applicant status can re-identify someone. Public examples should be generated from fully synthetic records rather than lightly redacted real records.

## Scanner limits

`scripts/privacy_scan.py` checks common identifiers, secret formats, workstation paths, legacy private-project terms and public-fixture invariants. It cannot understand every context or guarantee anonymization. Publication still requires human review.
