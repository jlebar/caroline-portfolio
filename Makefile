local:
	hugo serve -D

publish:
	# Assuming $USER and NFSN user are the same.
	hugo
	rsync --chmod=+rx --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:

stage:
	hugo --environment staging
	rsync --chmod=+rx --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:staging
