HUMAN-VOICE AUDIO FOR THE ATHENAZE COMPANION DECK (ai33.pro)

UPDATING FROM AN EARLIER KIT
  Copy the  audio  folder from your old kit folder into this folder, put key.txt here, and run
  python3 generate.py all . Files you already have are skipped, so only sentences that changed are sent
  (this update: 2,162 new sentences, about 57,000 characters). Then do step 5 below.
  If you no longer have the old audio folder, just run  all : it makes everything again.

What's here
  generate.py                                  the batch script (needs only Python 3.8+, nothing to install)
  audio_manifest.tsv                           3,657 sentences in modern spelling + the file name each one gets
  Athenaze_Companion_ch01-32_humanvoice.apkg   the deck, pointing at the new audio files (same notes, plus new ones)

0. Python
   Mac: open Terminal and type  python3 --version . If it isn't installed, macOS offers to install it; accept.
   Windows: install Python from python.org (tick "Add python.exe to PATH"), then use  python  instead of  python3 .

1. Put your ai33 API key into a file called  key.txt  in this folder (just the key, one line).
   Keep that file private; delete it when you're done.

2. Open a terminal in this folder and check the key:
       python3 generate.py credits

3. Test 20 sentences (costs a few hundred credits):
       python3 generate.py test
   Listen to the files in  audio_test/  (the texts are in _sentences.txt).
   Other voice:   python3 generate.py test --voice fishaudio_XXXX
   Slower:        python3 generate.py test --speed 0.9

4. Do everything (about 207,000 characters; probably 1–3 hours):
       python3 generate.py all
   Use the same --voice/--speed you chose in the test. You can stop it (Ctrl+C) and run the same command
   again at any time: finished files are kept, and sentences already sent are not paid for twice.
   If it reports errors:   python3 generate.py retry

5. Put the audio into Anki:
   - Close Anki, then run:   python3 generate.py install
     (it copies the files into Anki's media folder; if it can't find it, add  --media "<path to collection.media>")
   - Open Anki, File → Import → Athenaze_Companion_ch01-32_humanvoice.apkg
     The notes are the same as before, so they are updated in place and your review history stays.
   - Sync. Later, Tools → Check Media → "Delete Unused" removes the old eSpeak files.
