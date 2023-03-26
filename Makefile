
# This file is part of Wordform Email Reporter.
# check files to upload to gcp
check_files:
	gcloud meta list-files-for-upload

deploy:
	make freeze
	make deploy_function

# pipenv freeze > requirements.txt
freeze:
	pipenv run pip freeze > requirements.txt

# create pubsub topic
create_topic:
	gcloud pubsub topics create wordformemailreporter

# create cloud scheduler job
create_scheduler:
	gcloud scheduler jobs create pubsub wordformemailreporter \
	--schedule="0 7 * * *" \
	--topic=wordformemailreporter \
	--location=europe-north1 \
	--message-body="report" \
	--time-zone="Europe/Helsinki" \
	--description="Wordform Email Reporter"

# upload main.py and requirements.txt to the board using 
# gcloud cloud functions deploy
deploy_function:
	gcloud functions deploy wordformemailreporter \
	--gen2 \
	--region=europe-north1 \
	--runtime=python311 \
	--source=. \
	--entry-point=report  \
	--memory=128Mi \
	--env-vars-file=.env.yaml \
	--trigger-topic=wordformemailreporter \
	

# manually trigger the function to test it with the topic
trigger:
	gcloud pubsub topics publish wordformemailreporter --message="report"