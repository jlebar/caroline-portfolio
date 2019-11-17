local:
	hugo serve -D

publish:
	# Assuming $USER and NFSN user are the same.
	hugo
	rsync --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:

stage:
	hugo --environment staging
	rsync --omit-dir-times --progress -a public/ ${USER}_cslebar@ssh.phx.nearlyfreespeech.net:staging
