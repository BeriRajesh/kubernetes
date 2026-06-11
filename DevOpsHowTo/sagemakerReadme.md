## Steps to launch an AWS SageMaker notebook instance through AWS Service Catalog:
1. Sign-in to [OMC Central](https://omnicomgroup.okta.com). ([help?](https://s3-eu-west-1.amazonaws.com/static.annalect.com/howto/SignInOmcCentralOktaDashboard.pdf))
2. Select an AWS chicklet **OMG-Annalect-AWS** from the dashboard.
3. Choose **OMG-Annalect-AWS-Datascience** role from the presented list. It won't prompt to choose role if single role is allocated to your account.
4. Make sure that you're in us-east-1 (North Virgina) AWS Region. If not, in the menu bar, choose us-east-1 region.
5. Open [Service Catalog Product](https://console.aws.amazon.com/servicecatalog/home?region=us-east-1#/products) to see the products available for you to launch as an end-user.
6. Choose **SageMaker Notebooks**
7. Choose **Launch Product**. Specify the product name.
8. Choose v1.0.0, and choose **Next**. 
9. On the Parameters page, type the following and choose Next:
      * **InstanceName** – Type a name for your notebook instance.
      * **InstanceType** – Default: ml.t2.medium, choose the InstanceType based on your needs.
10. On the **TagOptions** page, choose **Next** (AWS Service Catalog automatically generates a mandatory tag here).
11. On the **Notifications** page, choose **Next**.
12. On the **Review page**, choose **Launch**
13. Wait for the status to change to Completed.
14. After the status changes to Available/Succeeded, navigate to [SageMaker Console](https://us-east-1.console.aws.amazon.com/sagemaker/home?region=us-east-1#/notebook-instances) and locate the newly created notebook.

If you see your Notebook Instance InService state, you're ready to **Build, Train, and Deploy a ML model**.

#### Use [SageMaker Console](https://us-east-1.console.aws.amazon.com/sagemaker/home?region=us-east-1#/notebook-instances) to manage and work through your notebook.
However, to terminate or upgrade the SageMaker instance, please go to [Service Catalog Product](https://console.aws.amazon.com/servicecatalog/home?region=us-east-1#/products).
We recommend to start the instance when you are actively using it, and stop it when finished.

Please contact [DevOps](mailto:devops@annalect.com?subject=Issues with SageMaker Notebook), in case of any issues.


