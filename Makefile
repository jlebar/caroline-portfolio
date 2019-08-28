all:
	hugo

stage: all
	rsync --omit-dir-times --progress -a public/ jlebar_jlebar-blog@ssh.phx.nearlyfreespeech.net:caroline-staging

