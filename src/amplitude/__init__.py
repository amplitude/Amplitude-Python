"""The official Amplitude Python SDK"""


from amplitude.client import Amplitude
from amplitude.event import BaseEvent, EventOptions, Identify, Revenue, IdentifyEvent, \
    GroupIdentifyEvent, RevenueEvent, Plan, IngestionMetadata
from amplitude.config import Config
from amplitude.constants import PluginType
from amplitude.plugin import EventPlugin, DestinationPlugin

# AI observability is available as a submodule
# Import with: from amplitude.ai import OpenAI, Anthropic, etc.
# or: from amplitude import ai
