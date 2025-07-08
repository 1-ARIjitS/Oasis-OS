// Frontend Integration Example for Oasis OS Workflow Execution
// This example shows how to integrate with the backend API

class WorkflowManager {
    constructor(apiBaseUrl = 'http://localhost:8000/api/v1') {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Execute a workflow with the user's query
     * @param {string} query - User's task description
     * @param {string} model - AI model to use (defaults to gpt-4.1)
     * @returns {Promise<string>} - Workflow ID
     */
    async executeWorkflow(query, model = 'gpt-4.1') {
        try {
            const response = await fetch(`${this.apiBaseUrl}/workflow/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    model: model
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.workflow_id;
        } catch (error) {
            console.error('Error executing workflow:', error);
            throw error;
        }
    }

    /**
     * Check workflow status
     * @param {string} workflowId - Workflow ID
     * @returns {Promise<object>} - Workflow status details
     */
    async getWorkflowStatus(workflowId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/workflow/${workflowId}/status`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting workflow status:', error);
            throw error;
        }
    }

    /**
     * Poll workflow status until completion
     * @param {string} workflowId - Workflow ID
     * @param {function} onStatusUpdate - Callback for status updates
     * @returns {Promise<object>} - Final workflow status
     */
    async pollWorkflowStatus(workflowId, onStatusUpdate = null) {
        return new Promise((resolve, reject) => {
            const pollInterval = setInterval(async () => {
                try {
                    const status = await this.getWorkflowStatus(workflowId);
                    
                    // Call status update callback if provided
                    if (onStatusUpdate) {
                        onStatusUpdate(status);
                    }

                    // Check if workflow is complete
                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        resolve(status);
                    } else if (status.status === 'failed' || status.status === 'cancelled') {
                        clearInterval(pollInterval);
                        reject(new Error(status.message));
                    }
                } catch (error) {
                    clearInterval(pollInterval);
                    reject(error);
                }
            }, 2000); // Poll every 2 seconds
        });
    }

    /**
     * Cancel a running workflow
     * @param {string} workflowId - Workflow ID
     * @returns {Promise<boolean>} - Success status
     */
    async cancelWorkflow(workflowId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/workflow/${workflowId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error cancelling workflow:', error);
            throw error;
        }
    }
}

// Example usage in your frontend component
class CustomWorkflowComponent {
    constructor() {
        this.workflowManager = new WorkflowManager();
        this.currentWorkflowId = null;
    }

    /**
     * Handle execute button click
     */
    async onExecuteButtonClick() {
        const queryInput = document.getElementById('workflow-query-input');
        const executeButton = document.getElementById('execute-button');
        const statusDisplay = document.getElementById('status-display');
        const notificationArea = document.getElementById('notification-area');

        const query = queryInput.value.trim();
        
        if (!query) {
            this.showNotification('Please enter a task description', 'error');
            return;
        }

        try {
            // Disable button and show loading state
            executeButton.disabled = true;
            executeButton.textContent = 'Executing...';
            statusDisplay.textContent = 'Starting workflow execution...';

            // Execute workflow with gpt-4.1
            this.currentWorkflowId = await this.workflowManager.executeWorkflow(query, 'gpt-4.1');
            
            // Poll for status updates
            const finalStatus = await this.workflowManager.pollWorkflowStatus(
                this.currentWorkflowId,
                (status) => {
                    // Update UI with current status
                    statusDisplay.textContent = status.message;
                    console.log('Workflow status:', status);
                }
            );

            // Workflow completed successfully
            this.showNotification('Workflow successfully executed', 'success');
            statusDisplay.textContent = 'Task completed successfully!';
            
            // Optional: Show execution logs
            if (finalStatus.logs) {
                console.log('Execution logs:', finalStatus.logs);
            }

        } catch (error) {
            console.error('Workflow execution failed:', error);
            this.showNotification(`Workflow failed: ${error.message}`, 'error');
            statusDisplay.textContent = 'Workflow execution failed';
        } finally {
            // Re-enable button
            executeButton.disabled = false;
            executeButton.textContent = 'Execute Query';
            this.currentWorkflowId = null;
        }
    }

    /**
     * Handle cancel button click
     */
    async onCancelButtonClick() {
        if (!this.currentWorkflowId) {
            return;
        }

        try {
            await this.workflowManager.cancelWorkflow(this.currentWorkflowId);
            this.showNotification('Workflow cancelled', 'warning');
        } catch (error) {
            console.error('Error cancelling workflow:', error);
            this.showNotification('Failed to cancel workflow', 'error');
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        const notificationArea = document.getElementById('notification-area');
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        notificationArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize the component when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const workflowComponent = new CustomWorkflowComponent();
    
    // Bind event listeners
    const executeButton = document.getElementById('execute-button');
    const cancelButton = document.getElementById('cancel-button');
    
    if (executeButton) {
        executeButton.addEventListener('click', () => workflowComponent.onExecuteButtonClick());
    }
    
    if (cancelButton) {
        cancelButton.addEventListener('click', () => workflowComponent.onCancelButtonClick());
    }
});

// Export for use in other modules
export { WorkflowManager, CustomWorkflowComponent }; 