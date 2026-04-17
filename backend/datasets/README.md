# Local Dataset Contract

Expected dataset layout for the local sign-language classifier:

```text
backend/datasets/sign_language_images/
  train/
    hello/
    yes/
    no/
    thanks/
    please/
    help/
  val/
    hello/
    yes/
    no/
    thanks/
    please/
    help/
  test/
    hello/
    yes/
    no/
    thanks/
    please/
    help/
```

Each class directory should contain cropped sign images or extracted video frames.

Recommended preparation steps:

1. Normalize all images to RGB.
2. Keep signer backgrounds diverse to reduce overfitting.
3. Reserve unseen signers for `test/` whenever possible.
4. Store augmentation scripts or source dataset notes in `docs/` rather than mixing them into the artifact folder.

Training command:

```bash
python -m backend.train --dataset-root backend/datasets/sign_language_images --artifact-dir backend/artifacts/models/local_sign_model
```

Evaluation command:

```bash
python -m backend.evaluate --dataset-root backend/datasets/sign_language_images --artifact-dir backend/artifacts/models/local_sign_model
```

