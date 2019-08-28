all:
	hugo

stage: all
	rsync --progress -a public/ jlebar_jlebar-blog@ssh.phx.nearlyfreespeech.net:caroline-staging
