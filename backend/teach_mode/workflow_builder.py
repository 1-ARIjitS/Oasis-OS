import json
import os
import gc
import time
from datetime import datetime
from groq import Groq
from pathlib import Path

class WorkflowBuilder:
    def __init__(self, session_dir, groq_api_key=None):
        # Accept either absolute path or just session_name
        if not os.path.isabs(session_dir):
            session_dir = Path(__file__).resolve().parent / "teach_sessions" / session_dir
        self.session_dir = str(session_dir)
        self.groq_api_key = groq_api_key
        self.groq_client = None  # Initialize as None
        self.workflow = {
            "metadata": {
                "session_name": os.path.basename(session_dir),
                "created_at": datetime.now().isoformat()
            },
            "steps": []
        }
        self.action_counter = 0
        
    def _get_groq_client(self):
        """Lazy initialization of Groq client with error handling"""
        if self.groq_client is None and self.groq_api_key:
            try:
                # Add delay to avoid conflicts with previous Groq usage
                time.sleep(0.5)
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"⚠️ Failed to initialize Groq client: {e}")
                self.groq_client = False  # Mark as failed
        return self.groq_client if self.groq_client != False else None
        
    def build_workflow(self):
        try:
            # Load session data
            json_path = os.path.join(self.session_dir, "session.json")
            if not os.path.exists(json_path):
                print(f"❌ session.json not found at {json_path}")
                return None
                
            with open(json_path) as f:
                session_data = json.load(f)
            
            # Create combined events list
            all_events = []
            all_events.extend(session_data.get('mouse_events', []))
            all_events.extend(session_data.get('key_events', []))
            all_events.extend(session_data.get('voice_commands', []))
            
            # Sort chronologically
            all_events.sort(key=lambda x: x.get('time', 0))
            
            # Process events
            current_step = None
            step_counter = 1
            last_action_time = 0
            action_threshold = 1.5  # Seconds between actions to create new step
            
            for event in all_events:
                try:
                    event_type = event.get('type', event.get('event_type', ''))
                    
                    # Skip modifier releases and moves
                    if event_type in ['modifier_release', 'move']:
                        continue
                        
                    # Check if we need to start a new step
                    if (current_step is None or 
                        (event.get('time', 0) - last_action_time > action_threshold)):
                        
                        if current_step and current_step.get('actions'):
                            self.workflow['steps'].append(current_step)
                        
                        # Create new step
                        current_step = {
                            'name': f"Step {step_counter}",
                            'description': f"Automated action sequence {step_counter}",
                            'actions': []
                        }
                        step_counter += 1
                    
                    # Handle voice commands
                    if event_type == 'voice_command':
                        text = event.get('text', '').strip()
                        if text:
                            current_step['actions'].append({
                                'id': self._next_action_id(),
                                'type': 'voice_command',
                                'text': text,
                                'timestamp': event.get('time', 0)
                            })
                            last_action_time = event.get('time', 0)
                    
                    # Handle mouse events
                    elif event_type == 'click':
                        current_step['actions'].append({
                            'id': self._next_action_id(),
                            'type': 'click',
                            'location': [event.get('x', 0), event.get('y', 0)],
                            'button': event.get('button', 'left')
                        })
                        last_action_time = event.get('time', 0)
                    
                    # Handle keyboard events
                    elif event_type == 'type':
                        text = event.get('text', '')
                        if text:
                            current_step['actions'].append({
                                'id': self._next_action_id(),
                                'type': 'type',
                                'text': text
                            })
                            last_action_time = event.get('time', 0)
                    
                    elif event_type == 'keypress':
                        key = event.get('key', '')
                        if key in ['enter', 'tab', 'esc', 'space', 'backspace', 'delete']:
                            current_step['actions'].append({
                                'id': self._next_action_id(),
                                'type': 'key_press',
                                'key': key
                            })
                            last_action_time = event.get('time', 0)
                    
                    # Handle modifier keys
                    elif event_type == 'modifier_press':
                        key = event.get('key', '')
                        next_event = self._get_next_event(all_events, event.get('time', 0))
                        if next_event and next_event.get('type') == 'keypress':
                            next_key = next_event.get('key', '')
                            
                            # Handle copy/paste as special actions
                            if key in ['ctrl', 'cmd'] and next_key in ['c', 'v']:
                                action_type = 'copy' if next_key == 'c' else 'paste'
                                current_step['actions'].append({
                                    'id': self._next_action_id(),
                                    'type': action_type
                                })
                                # Skip processing the next keypress
                                next_event['processed'] = True
                                last_action_time = event.get('time', 0)
                            
                            # Handle other hotkey combinations
                            elif key in ['ctrl', 'cmd'] and next_key in ['space', 'enter', 'tab']:
                                # Create hotkey action
                                current_step['actions'].append({
                                    'id': self._next_action_id(),
                                    'type': 'hotkey',
                                    'keys': [key, next_key]
                                })
                                # Skip processing the next keypress
                                next_event['processed'] = True
                                last_action_time = event.get('time', 0)
                                
                except Exception as e:
                    print(f"⚠️ Error processing event: {e}")
                    continue
            
            # Add the last step if valid
            if current_step and current_step.get('actions'):
                self.workflow['steps'].append(current_step)
            
            # Clear session data from memory
            session_data = None
            all_events = None
            gc.collect()
            
            # Optimize with Groq if API key is available
            # if self.groq_api_key and len(self.workflow['steps']) > 0:
            #     print("\n🧠 Optimizing workflow with Groq AI...")
            #     try:
            #         optimized = self.optimize_with_groq(self.workflow)
            #         if optimized:
            #             self.workflow = optimized
            #             print("✅ AI optimization applied")
            #         else:
            #             print("⚠️ AI optimization failed, using original workflow")
            #     except Exception as e:
            #         print(f"⚠️ AI optimization error: {e}")
            
            # Save workflow
            workflow_path = os.path.join(self.session_dir, "workflow.json")
            with open(workflow_path, 'w') as f:
                json.dump(self.workflow, f, indent=2)
                
            print(f"✅ Workflow saved to {workflow_path}")
            self.workflow['metadata']['total_steps'] = len(self.workflow['steps'])
            self.workflow['metadata']['total_actions'] = self.action_counter
            
            return self.workflow
            
        except Exception as e:
            print(f"❌ Error building workflow: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Cleanup
            if self.groq_client and self.groq_client != False:
                self.groq_client = None
            gc.collect()
    
    def _next_action_id(self):
        self.action_counter += 1
        return f"action_{self.action_counter}"
    
    def _get_next_event(self, events, current_time):
        """Get next event after current time"""
        for event in events:
            if event['time'] > current_time and not event.get('processed', False):
                return event
        return None

    def optimize_with_groq(self, workflow):
        """Use Groq to simplify and optimize workflows"""
        try:
            # Get Groq client with lazy initialization
            client = self._get_groq_client()
            if not client:
                print("⚠️ Groq client not available for optimization")
                return None
            
            # Prepare a smaller prompt to avoid token limits
            workflow_summary = {
                "metadata": workflow.get("metadata", {}),
                "steps_count": len(workflow.get("steps", [])),
                "sample_steps": workflow.get("steps", [])[:3]  # Only first 3 steps
            }
            
            # Prepare prompt
            prompt = (
                "Optimize this automation workflow by removing redundant steps and improving efficiency. "
                "Return the same structure but optimized. Keep all original functionality:\n\n"
                f"{json.dumps(workflow_summary, indent=2)}"
            )
            
            # Add timeout and retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Send to Groq API with shorter timeout
                    response = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert in process automation. Return optimized workflow as JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        model="llama3-8b-8192",  # Use smaller, faster model
                        temperature=0.1,
                        max_tokens=2048,  # Limit response size
                        response_format={"type": "json_object"}
                    )
                    
                    # Parse and return optimized workflow
                    content = response.choices[0].message.content
                    if content:
                        optimized = json.loads(content)
                        
                        # Preserve original steps if optimization didn't work properly
                        if not optimized.get('steps'):
                            optimized['steps'] = workflow.get('steps', [])
                        
                        # Add optimization metadata
                        optimized['metadata'] = workflow.get('metadata', {})
                        optimized['metadata']['optimized'] = True
                        optimized['metadata']['optimized_at'] = datetime.now().isoformat()
                        
                        return optimized
                    else:
                        print(f"⚠️ Empty response from Groq (attempt {attempt + 1})")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing error (attempt {attempt + 1}): {e}")
                except Exception as e:
                    print(f"⚠️ Groq API error (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
            
            print("⚠️ All optimization attempts failed")
            return None
            
        except Exception as e:
            print(f"⚠️ Groq optimization failed: {str(e)}")
            return None