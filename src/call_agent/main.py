import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import streamlit as st
from pydantic import BaseModel, EmailStr, Field, ValidationError
from crewai import Agent, Task, Crew, Process
from enum import Enum
import re
import json
import asyncio
from functools import lru_cache
from datetime import datetime as dt

# Configure logging with proper format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enhanced Models with Validation
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"
    FOLLOWUP = "followup"
    RESCHEDULED = "rescheduled"

class LeadPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(hash(dt.now())))
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    email: EmailStr
    interest: str = Field(..., min_length=1, max_length=500)
    status: LeadStatus = LeadStatus.NEW
    priority: LeadPriority = LeadPriority.MEDIUM
    created_at: dt = Field(default_factory=dt.now)
    last_contacted: Optional[dt] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    budget: Optional[float] = None
    next_followup: Optional[dt] = None

    def calculate_score(self) -> float:
        """Calculate lead score based on various factors"""
        score = 0
        if self.budget and self.budget > 1000:
            score += 20
        if self.last_contacted and (dt.now() - self.last_contacted).days < 7:
            score += 10
        if self.status == LeadStatus.QUALIFIED:
            # Add score for qualified leads
            score += 30  # Increase score by 30 points for qualified leads
        if self.priority == LeadPriority.HIGH:
            score += 25
        return score

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(hash(dt.now())))
    datetime: dt
    details: str
    lead_id: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    duration_minutes: int = 30
    location: Optional[str] = None
    reminder_sent: bool = False
    created_at: dt = Field(default_factory=dt.now)
    updated_at: dt = Field(default_factory=dt.now)
    notes: Optional[str] = None

    def is_conflicting(self, other: 'Appointment') -> bool:
        """Check if this appointment conflicts with another"""
        my_end = self.datetime + timedelta(minutes=self.duration_minutes)
        other_end = other.datetime + timedelta(minutes=other.duration_minutes)
        return (self.datetime <= other.datetime < my_end) or (other.datetime <= self.datetime < other_end)

class ConversationType(str, Enum):
    INQUIRY = "inquiry"
    FOLLOWUP = "followup"
    SCHEDULING = "scheduling"
    FEEDBACK = "feedback"
    SUPPORT = "support"

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(hash(dt.now())))
    user_input: str
    context: str = ""
    conversation_type: ConversationType
    timestamp: dt = Field(default_factory=dt.now)
    lead_id: Optional[str] = None
    sentiment_score: Optional[float] = None
    ai_response: Optional[str] = None
    next_actions: List[str] = []

# Enhanced AI Agents
class LeadGenerationExpert(Agent):
    def __init__(self):
        super().__init__(
            role='Lead Generation Specialist',
            goal='Generate and qualify leads for fertility services',
            backstory="""Expert in identifying and engaging potential clients for fertility services. 
            Specializes in lead scoring, qualification, and nurturing with deep knowledge of fertility and family-building services.""",
            verbose=True,
            allow_delegation=True
        )

    async def identify_potential_leads(self, criteria: Dict[str, Any]) -> List[Lead]:
        """Identify potential leads based on given criteria"""
        leads = []
        # Implement lead identification logic
        for lead in Database.leads:
            score = lead.calculate_score()
            if 'fertility_interest' in criteria and score > 75:
                leads.append(lead)
        return leads

    async def qualify_lead(self, lead: Lead) -> Dict[str, Any]:
        """Qualify a lead based on specific criteria"""
        qualification = {
            'interest_level': self.analyze_interest_level(lead),
            'budget_match': self.evaluate_budget_fit(lead),
            'service_match': self.determine_service_alignment(lead),
            'readiness': self.assess_readiness(lead)
        }
        return qualification

class CustomerFollowUpSpecialist(Agent):
    def __init__(self):
        super().__init__(
            role='Follow-up Specialist',
            goal='Maintain engagement and nurture client relationships',
            backstory="""Expert in personalized client engagement and relationship building. 
            Focuses on maintaining client interest and providing valuable information about fertility services.""",
            verbose=True,
            allow_delegation=True
        )

    async def create_follow_up_plan(self, lead: Lead) -> Dict[str, Any]:
        """Create a personalized follow-up plan"""
        plan = {
            'initial_contact': dt.now(),
            'follow_up_schedule': self.generate_schedule(lead),
            'communication_preferences': lead.get_preferences(),
            'educational_content': self.select_relevant_content(lead)
        }
        return plan

    async def handle_follow_up(self, conversation: Conversation) -> str:
        """Handle follow-up conversation"""
        context = self.analyze_conversation_context(conversation)
        response = self.generate_personalized_response(context)
        next_steps = self.determine_next_steps(conversation)
        return response

class AppointmentSchedulingExpert(Agent):
    def __init__(self):
        super().__init__(
            role='Scheduling Specialist',
            goal='Efficiently manage appointment scheduling and calendar optimization',
            backstory="""Expert in appointment scheduling and calendar management for fertility services. 
            Ensures optimal scheduling while considering patient preferences and clinical availability.""",
            verbose=True,
            allow_delegation=True
        )

    async def schedule_appointment(self, lead: Lead, preferred_time: dt) -> Appointment:
        """Schedule an appointment based on preferences"""
        available_slots = await self.suggest_time_slots(preferred_time)
        if not available_slots:
            raise ValueError("No available slots found")
        
        appointment = Appointment(
            datetime=available_slots[0],
            lead_id=lead.id,
            details=f"Initial consultation for {lead.name}",
            status=AppointmentStatus.SCHEDULED
        )
        return appointment

    async def handle_rescheduling(self, appointment: Appointment, new_time: dt) -> Appointment:
        """Handle appointment rescheduling"""
        if appointment.is_conflicting(new_time):
            raise ValueError("Time slot conflicts with existing appointment")
        
        appointment.datetime = new_time
        appointment.status = AppointmentStatus.RESCHEDULED
        return appointment

    async def analyze_lead(self, lead: Lead) -> Dict[str, Any]:
        """Analyze lead and provide insights"""
        score = lead.calculate_score()
        suggested_actions = []
        if score > 75:
            suggested_actions.append("Immediate follow-up required")
        elif score > 50:
            suggested_actions.append("Schedule consultation")
        return {
            "score": score,
            "suggested_actions": suggested_actions,
            "priority": "high" if score > 75 else "medium"
        }

class AppointmentManager(Agent):
    def __init__(self):
        super().__init__(
            role='Appointment Manager',
            goal='Optimize appointment scheduling and management',
            backstory='Expert in efficient scheduling and calendar management',
            verbose=True,
            allow_delegation=True
        )

    async def suggest_time_slots(self, requested_date: dt) -> List[dt]:
        """Suggest available time slots"""
        available_slots = []
        start_hour = 9  # 9 AM
        end_hour = 17   # 5 PM
        for hour in range(start_hour, end_hour):
            slot = requested_date.replace(hour=hour, minute=0)
            if not any(appt.is_conflicting(Appointment(datetime=slot, details="temp")) 
                      for appt in Database.appointments):
                available_slots.append(slot)
        return available_slots

class CustomerEngagement(Agent):
    def __init__(self):
        super().__init__(
            role='Customer Engagement Specialist',
            goal='Drive personalized client engagement',
            backstory='Expert in maintaining client relationships with empathy',
            verbose=True,
            allow_delegation=True
        )

    async def analyze_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Analyze conversation and provide insights"""
        # Simple sentiment analysis based on keywords
        positive_words = {'great', 'happy', 'excited', 'interested'}
        negative_words = {'concerned', 'worried', 'unsure', 'expensive'}
        
        words = conversation.user_input.lower().split()
        sentiment = sum(1 for w in words if w in positive_words) - sum(1 for w in words if w in negative_words)
        
        return {
            "sentiment": sentiment,
            "urgent": any(w in words for w in {'urgent', 'asap', 'emergency'}),
            "suggested_response": self.generate_response(conversation)
        }

    def generate_response(self, conversation: Conversation) -> str:
        """Generate appropriate response based on conversation type"""
        responses = {
            ConversationType.INQUIRY: "Thank you for your interest. I'd be happy to provide more information.",
            ConversationType.FOLLOWUP: "I hope you're doing well. I wanted to follow up on our previous conversation.",
            ConversationType.SCHEDULING: "I can help you schedule an appointment at your convenience.",
            ConversationType.FEEDBACK: "Thank you for your feedback. It helps us improve our services.",
            ConversationType.SUPPORT: "I'm here to help. Please let me know your concerns."
        }
        return responses.get(conversation.conversation_type, "How can I assist you today?")

# Enhanced Database with Better Structure and Operations
class Database:
    appointments: List[Appointment] = []
    conversations: List[Conversation] = []
    leads: List[Lead] = []
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def add_lead(cls, lead: Lead) -> str:
        async with cls._lock:
            cls.leads.append(lead)
            logger.info(f"New lead added: {lead.name}")
            return lead.id

    @classmethod
    async def update_lead(cls, lead_id: str, **kwargs) -> bool:
        async with cls._lock:
            for idx, lead in enumerate(cls.leads):
                if lead.id == lead_id:
                    updated_lead = lead.model_copy(update=kwargs)
                    cls.leads[idx] = updated_lead
                    logger.info(f"Lead updated: {lead_id}")
                    return True
            return False

    @classmethod
    async def add_appointment(cls, appointment: Appointment) -> Tuple[bool, str]:
        async with cls._lock:
            # Check for conflicts
            for existing_appt in cls.appointments:
                if appointment.is_conflicting(existing_appt):
                    return False, "Appointment time conflicts with existing appointment"
            cls.appointments.append(appointment)
            logger.info(f"New appointment scheduled: {appointment.datetime}")
            return True, appointment.id

    @classmethod
    async def get_lead_appointments(cls, lead_id: str) -> List[Appointment]:
        return [appt for appt in cls.appointments if appt.lead_id == lead_id]

# Enhanced CrewAI Setup
@lru_cache()
def create_crew() -> Crew:
    lead_gen = LeadGenerationExpert()
    appt_manager = AppointmentManager()
    engagement = CustomerEngagement()

    tasks = [
        Task(
            description="Identify and analyze new leads",
            agent=lead_gen
        ),
        Task(
            description="Manage appointments and suggest optimal scheduling",
            agent=appt_manager
        ),
        Task(
            description="Handle customer engagement and generate responses",
            agent=engagement
        )
    ]

    return Crew(
        agents=[lead_gen, appt_manager, engagement],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )

# Enhanced Streamlit UI Functions
def show_leads_page():
    st.header("👥 Leads Management")
    
    with st.expander("Add New Lead", expanded=False):
        with st.form("new_lead"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name")
                email = st.text_input("Email")
                priority = st.selectbox("Priority", options=[p.value for p in LeadPriority])
            with col2:
                phone = st.text_input("Phone")
                interest = st.text_area("Interest")
                source = st.text_input("Source")
            
            if st.form_submit_button("Add Lead"):
                try:
                    lead = Lead(
                        name=name,
                        phone=phone,
                        email=email,
                        interest=interest,
                        priority=priority,
                        source=source
                    )
                    asyncio.run(Database.add_lead(lead))
                    st.success("✅ Lead added successfully!")
                    
                    # Analyze lead using AI
                    insights = asyncio.run(LeadGenerationExpert().analyze_lead(lead))
                    if insights["score"] > 75:
                        st.warning("🔥 High-priority lead detected! Immediate action recommended.")
                        
                except ValidationError as e:
                    st.error(f"❌ Error adding lead: {str(e)}")

    if Database.leads:
        # Sort leads by score
        sorted_leads = sorted(Database.leads, key=lambda x: x.calculate_score(), reverse=True)
        for lead in sorted_leads:
            with st.expander(f"📋 Lead: {lead.name} (Score: {lead.calculate_score():.0f})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"📱 Phone: {lead.phone}")
                    st.write(f"📧 Email: {lead.email}")
                with col2:
                    st.write(f"💡 Interest: {lead.interest}")
                    st.write(f"📊 Status: {lead.status}")
                with col3:
                    st.write(f"⭐ Priority: {lead.priority}")
                    st.write(f"📍 Source: {lead.source or 'N/A'}")
                
                # Show appointments for this lead
                appointments = asyncio.run(Database.get_lead_appointments(lead.id))
                if appointments:
                    st.write("📅 Appointments:")
                    for appt in appointments:
                        st.write(f"- {appt.datetime.strftime('%Y-%m-%d %H:%M')} ({appt.status})")

def show_appointments_page():
    st.header("📅 Appointments Management")
    
    with st.expander("Schedule New Appointment", expanded=False):
        with st.form("new_appointment"):
            date = st.date_input("Date")
            time = st.time_input("Time")
            details = st.text_area("Details")
            duration = st.number_input("Duration (minutes)", min_value=15, value=30, step=15)
            location = st.text_input("Location")
            
            if st.form_submit_button("Schedule Appointment"):
                try:
                    appointment_datetime = dt.combine(date, time)
                    appointment = Appointment(
                        datetime=appointment_datetime,
                        details=details,
                        duration_minutes=duration,
                        location=location
                    )
                    
                    success, result = asyncio.run(Database.add_appointment(appointment))
                    if success:
                        st.success("✅ Appointment scheduled successfully!")
                    else:
                        st.error(f"❌ Error scheduling appointment: {result}")
                except ValidationError as e:
                    st.error(f"❌ Error scheduling appointment: {str(e)}")

    if Database.appointments:
        # Sort appointments by datetime
        sorted_appointments = sorted(Database.appointments, key=lambda x: x.datetime)
        for appointment in sorted_appointments:
            with st.expander(f"📆 Appointment: {appointment.datetime.strftime('%Y-%m-%d %H:%M')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📝 Details: {appointment.details}")
                    st.write(f"⏱️ Duration: {appointment.duration_minutes} minutes")
                with col2:
                    st.write(f"📍 Location: {appointment.location or 'N/A'}")
                    st.write(f"📊 Status: {appointment.status}")
                
                if not appointment.reminder_sent and appointment.datetime - dt.now() <= timedelta(days=1):
                    st.warning("⚠️ Reminder needed!")

def show_conversations_page():
    st.header("💬 Conversations")
    
    with st.form("new_conversation"):
        user_input = st.text_area("Message")
        conv_type = st.selectbox("Conversation Type", options=[t.value for t in ConversationType])
        
        if st.form_submit_button("Send"):
            try:
                conversation = Conversation(
                    user_input=user_input,
                    conversation_type=conv_type
                )
                
                # Analyze conversation using AI
                engagement_specialist = CustomerEngagement()
                analysis = asyncio.run(engagement_specialist.analyze_conversation(conversation))
                
                conversation.sentiment_score = analysis["sentiment"]
                conversation.ai_response = analysis["suggested_response"]
                
                Database.conversations.append(conversation)
                st.success("✉️ Message sent!")
                
                if analysis["urgent"]:
                    st.warning("🚨 Urgent response needed!")
                
                st.info(f"🤖 AI Response: {conversation.ai_response}")
                
            except ValidationError as e:
                st.error(f"❌ Error processing message: {str(e)}")

    if Database.conversations:
        for conversation in reversed(Database.conversations):
            with st.expander(f"💬 Conversation at {conversation.timestamp.strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"👤 User: {conversation.user_input}")
                st.write(f"🤖 AI: {conversation.ai_response}")
                st.write(f"📊 Sentiment Score: {conversation.sentiment_score}")
                st.write(f"📋 Type: {conversation.conversation_type}")

def main():
    st.set_page_config(
        page_title="FemTech AI Receptionist",
        page_icon="👩‍⚕️",
        layout="wide"
    )
    
    st.title("🏥 FemTech AI Receptionist")
    
    # Initialize session state
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Sidebar navigation
    menu = st.sidebar.selectbox(
        "Menu",
        ["Leads", "Appointments", "Conversations"],
        key="navigation"
    )

    # Display statistics in sidebar
    st.sidebar.markdown("### 📊 Statistics")
    st.sidebar.write(f"Total Leads: {len(Database.leads)}")
    st.sidebar.write(f"Active Appointments: {len([a for a in Database.appointments if a.status == AppointmentStatus.SCHEDULED])}")
    st.sidebar.write(f"Conversations Today: {len([c for c in Database.conversations if c.timestamp.date() == dt.now().date()])}")

    if menu == "Leads":
        show_leads_page()
    elif menu == "Appointments":
        show_appointments_page()
    else:
        show_conversations_page()

if __name__ == "__main__":
    main()
