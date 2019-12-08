.PHONY: images

images:
	python3 compress-images.py

hugo-prereqs: images

local: hugo-prereqs
	hugo serve -D

publish: hugo-prereqs
	# Assuming $USER and NFSN user are the same.
	hugo
	rsync --chmod=+rx --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:

stage: hugo-prereqs
	hugo --environment staging
	rsync --chmod=+rx --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:staging

delete-stage:
	rsync --chmod=+rx --omit-dir-times --progress -a /dev/null ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:staging
