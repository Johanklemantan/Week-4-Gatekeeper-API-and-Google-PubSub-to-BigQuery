
echo "Create pubsub topic"
gcloud pubsub topics create week4topic
echo "Create pubsub subscriptions"
gcloud pubsub subscriptions create subscription-week4subscription --topic=week4topic