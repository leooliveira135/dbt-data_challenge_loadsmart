Welcome to your new dbt project!

aws athena create-data-catalog \
    --name aws-star-schema \
    --type GLUE \
    --description "Custom Glue catalog" \
    --parameters catalog-id="552738622317" \
    --region us-east-1


### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices
