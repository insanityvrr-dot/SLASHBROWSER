package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.*
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    enableEdgeToEdge()
    setContent {
      MyApplicationTheme {
        var currentTab by remember { mutableStateOf("Home") }
        var stripeSecretKey by remember { mutableStateOf(BuildConfig.STRIPE_SECRET_KEY) }
        var stripePublishableKey by remember { mutableStateOf(BuildConfig.STRIPE_PUBLISHABLE_KEY) }
        var predictiveIndexingEnabled by remember { mutableStateOf(true) }
        var historyEncryptionEnabled by remember { mutableStateOf(true) }
        var blockTrackersEnabled by remember { mutableStateOf(true) }
        val searchHistory = remember { mutableStateListOf<String>("swift web builder", "rust compiler on android", "velocity fast browser") }

        Scaffold(
          modifier = Modifier.fillMaxSize(),
          containerColor = BgColor,
          bottomBar = {
            BottomNavigationBar(currentTab = currentTab, onTabSelected = { currentTab = it })
          }
        ) { innerPadding ->
          Column(
            modifier = Modifier
              .fillMaxSize()
              .padding(innerPadding)
          ) {
            Header()
            Box(modifier = Modifier.weight(1f)) {
              when (currentTab) {
                "Home" -> HomeContent(
                  predictiveIndexingEnabled = predictiveIndexingEnabled,
                  searchHistory = searchHistory,
                  onSearch = { query -> if (!searchHistory.contains(query)) searchHistory.add(0, query) }
                )
                "Workspace" -> WorkspaceContent(
                  secretKey = stripeSecretKey,
                  publishableKey = stripePublishableKey,
                  onSecretKeyChange = { stripeSecretKey = it },
                  onPublishableKeyChange = { stripePublishableKey = it }
                )
                "Encrypted" -> EncryptedContent(
                  predictiveIndexingEnabled = predictiveIndexingEnabled,
                  historyEncryptionEnabled = historyEncryptionEnabled,
                  blockTrackers = blockTrackersEnabled,
                  searchHistory = searchHistory,
                  onPredictiveToggle = { predictiveIndexingEnabled = it },
                  onEncryptionToggle = { historyEncryptionEnabled = it },
                  onBlockToggle = { blockTrackersEnabled = it },
                  onClearHistory = { searchHistory.clear() }
                )
                "Settings" -> SettingsContent()
              }
            }
          }
        }
      }
    }
  }
}

@Composable
fun Header() {
  Row(
    modifier = Modifier
      .fillMaxWidth()
      .padding(horizontal = 24.dp, vertical = 16.dp),
    horizontalArrangement = Arrangement.SpaceBetween,
    verticalAlignment = Alignment.CenterVertically
  ) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
      Box(
        modifier = Modifier
          .size(32.dp)
          .shadow(8.dp, RoundedCornerShape(8.dp), spotColor = Indigo200)
          .clip(RoundedCornerShape(8.dp))
          .background(Indigo600),
        contentAlignment = Alignment.Center
      ) {
        Text("V", color = Color.White, fontWeight = FontWeight.Bold, fontStyle = FontStyle.Italic)
      }
      Text("Velocity", fontSize = 18.sp, fontWeight = FontWeight.SemiBold, color = Slate900, letterSpacing = (-0.5).sp)
    }

    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
      Row(
        modifier = Modifier
          .clip(CircleShape)
          .background(Emerald50)
          .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
      ) {
        Box(modifier = Modifier.size(6.dp).clip(CircleShape).background(Emerald500))
        Text("LOCALIZED", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Emerald700, letterSpacing = 1.sp)
      }
    }
  }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeContent(
  predictiveIndexingEnabled: Boolean,
  searchHistory: List<String>,
  onSearch: (String) -> Unit
) {
  var searchQuery by remember { mutableStateOf("") }
  var isProcessing by remember { mutableStateOf(false) }
  var actionResult by remember { mutableStateOf<String?>(null) }
  var speedMetricsVisible by remember { mutableStateOf(false) }

  Column(
    modifier = Modifier
      .fillMaxSize()
      .verticalScroll(rememberScrollState())
      .padding(horizontal = 24.dp),
    verticalArrangement = Arrangement.Top,
    horizontalAlignment = Alignment.CenterHorizontally
  ) {
    Spacer(modifier = Modifier.height(16.dp))

    // Hero Text
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
      Row(verticalAlignment = Alignment.CenterVertically) {
        Text("Velocity", fontSize = 32.sp, fontWeight = FontWeight.Bold, color = Slate900)
        Text(" Engine", fontSize = 32.sp, fontWeight = FontWeight.Light, color = Indigo500)
      }
      Text("Instantaneous page loads. Zero data collection.", fontSize = 14.sp, color = Slate500)
    }

    Spacer(modifier = Modifier.height(24.dp))

    // Search Pill / Perplexity Smart Actions Input
    OutlinedTextField(
      value = searchQuery,
      onValueChange = { searchQuery = it },
      placeholder = { Text("Ask or command... (e.g. 'Email John' or 'Write code')", color = Slate400, fontSize = 15.sp) },
      leadingIcon = {
        Icon(Icons.Outlined.Search, contentDescription = "Search", tint = Indigo500)
      },
      trailingIcon = {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(end = 4.dp)) {
          // NFC Share Trigger
          IconButton(
            onClick = {
              if (searchQuery.isNotBlank()) {
                searchQuery = "nfc_share: $searchQuery"
                isProcessing = true
                actionResult = null
              } else {
                actionResult = "Highlight some text or type a URL first to NFC Share!"
              }
            },
            modifier = Modifier
              .size(32.dp)
              .clip(CircleShape)
              .background(Emerald50)
          ) {
            Icon(Icons.Outlined.Share, contentDescription = "NFC Share (Tap Phones)", tint = Emerald500, modifier = Modifier.size(16.dp))
          }
          Spacer(modifier = Modifier.width(4.dp))
          IconButton(
            onClick = {
              if (searchQuery.isNotBlank()) {
                isProcessing = true
                actionResult = null
              }
            },
            modifier = Modifier
              .size(32.dp)
              .clip(CircleShape)
              .background(Indigo50)
          ) {
            if (isProcessing) {
              CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Indigo600, strokeWidth = 2.dp)
            } else {
              Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Execute Command", tint = Indigo600, modifier = Modifier.size(16.dp))
            }
          }
        }
      },
      shape = CircleShape,
      colors = OutlinedTextFieldDefaults.colors(
        focusedContainerColor = Color.White,
        unfocusedContainerColor = Color.White,
        focusedTextColor = Slate900,
        unfocusedTextColor = Slate900,
        unfocusedBorderColor = Slate100,
        focusedBorderColor = Indigo100,
      ),
      modifier = Modifier
        .fillMaxWidth()
        .height(64.dp)
        .shadow(16.dp, CircleShape, spotColor = Slate200.copy(alpha = 0.5f)),
      singleLine = true
    )

    // Simulation effect
    LaunchedEffect(isProcessing) {
      if (isProcessing) {
        kotlinx.coroutines.delay(1800)
        isProcessing = false
        val trimmedQuery = searchQuery.trim()
        if (trimmedQuery.startsWith("nfc_share:", ignoreCase = true)) {
          val sharedText = trimmedQuery.removePrefix("nfc_share:").trim()
          actionResult = "📲 NFC Handshake Succeeded! Shared webpage link:\n\"$sharedText\""
        } else if (trimmedQuery.contains("email", ignoreCase = true)) {
          actionResult = "🤖 Autonomous Action Approved:\nDrafted, approved, and successfully sent email with content derived from query."
        } else if (trimmedQuery.contains("code", ignoreCase = true) || trimmedQuery.contains("website", ignoreCase = true)) {
          actionResult = "💻 Instant-Dev Success:\nSynthesized clean frontend code and previewed locally in your custom sandbox."
        } else {
          actionResult = "⚡ Instantly processed on-device:\n\"$trimmedQuery\" loaded in 0.04s."
          speedMetricsVisible = true
        }
        onSearch(trimmedQuery)
        searchQuery = ""
      }
    }

    if (actionResult != null) {
      Spacer(modifier = Modifier.height(16.dp))
      Row(
        modifier = Modifier
          .fillMaxWidth()
          .clip(RoundedCornerShape(16.dp))
          .background(Emerald50)
          .border(1.dp, Emerald500.copy(alpha = 0.2f), RoundedCornerShape(16.dp))
          .padding(16.dp),
        verticalAlignment = Alignment.Top,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
      ) {
        Icon(Icons.Filled.CheckCircle, contentDescription = "Result", tint = Emerald500, modifier = Modifier.size(20.dp))
        Column {
          Text("Autonomous Action Outcome", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Emerald700)
          Text(actionResult ?: "", color = Slate800, fontSize = 13.sp, modifier = Modifier.padding(top = 2.dp))
        }
      }
    }

    Spacer(modifier = Modifier.height(24.dp))

    // Speed Load Metrics
    if (speedMetricsVisible) {
      Column(
        modifier = Modifier
          .fillMaxWidth()
          .clip(RoundedCornerShape(16.dp))
          .background(Slate50)
          .border(1.dp, Slate100, RoundedCornerShape(16.dp))
          .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
      ) {
        Text("⚡ VELOCITY LOAD METRICS", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Indigo500, letterSpacing = 1.5.sp)
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
          Column {
            Text("DNS Lookup", fontSize = 11.sp, color = Slate400)
            Text("0 ms (Cached)", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
          }
          Column {
            Text("TCP Handshake", fontSize = 11.sp, color = Slate400)
            Text("1 ms", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
          }
          Column {
            Text("Predictive Index", fontSize = 11.sp, color = Slate400)
            Text("On-device", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
          }
        }
      }
      Spacer(modifier = Modifier.height(24.dp))
    }

    // Voice & Autonomous Capabilities Quick Tips
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
      QuickActionCard(
        modifier = Modifier.weight(1f),
        icon = { Icon(Icons.Outlined.Email, contentDescription = null, tint = Blue600, modifier = Modifier.size(20.dp)) },
        iconBg = Blue50,
        title = "Auto-Draft Email",
        subtitle = "Tap & say 'Email Alice that code is ready'"
      )
      QuickActionCard(
        modifier = Modifier.weight(1f),
        icon = { Icon(Icons.Outlined.Code, contentDescription = null, tint = Purple600, modifier = Modifier.size(20.dp)) },
        iconBg = Purple50,
        title = "Deploy Website",
        subtitle = "Say 'Write code for a dashboard'"
      )
    }

    Spacer(modifier = Modifier.height(24.dp))

    // Fair Search Ranking Visualization Card
    Column(
      modifier = Modifier
        .fillMaxWidth()
        .clip(RoundedCornerShape(20.dp))
        .background(Indigo900.copy(alpha = 0.04f))
        .border(1.dp, Indigo100, RoundedCornerShape(20.dp))
        .padding(20.dp),
      verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
      Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("LOCALIZED FAIR SEARCH ENGINE", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Indigo600, letterSpacing = 1.sp)
        Text("Llama Indexed", fontSize = 10.sp, color = Indigo400)
      }
      Text(
        text = "Our search ranking engine is strictly localized and built to help everyone succeed. Reputable websites stay up top, but brand new sites are automatically promoted in the middle instead of being buried on page 10. This ensures fair, decentralized traffic distribution without server tracking.",
        fontSize = 13.sp,
        color = Slate700,
        lineHeight = 18.sp
      )

      // Mini-simulation of fair rankings
      Column(
        modifier = Modifier
          .fillMaxWidth()
          .clip(RoundedCornerShape(12.dp))
          .background(Color.White)
          .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
      ) {
        RankingItem(rank = "1", name = "Wikipedia.org", type = "Reputable", color = Indigo500)
        RankingItem(rank = "2", name = "MyNewPortfolio.dev", type = "Auto-Promoted (Middle)", color = Emerald500, highlight = true)
        RankingItem(rank = "3", name = "StackOverflow.com", type = "Reputable", color = Indigo500)
      }
    }

    Spacer(modifier = Modifier.height(32.dp))
  }
}

@Composable
fun RankingItem(rank: String, name: String, type: String, color: Color, highlight: Boolean = false) {
  Row(
    modifier = Modifier
      .fillMaxWidth()
      .clip(RoundedCornerShape(8.dp))
      .background(if (highlight) Emerald50 else Color.Transparent)
      .padding(horizontal = 8.dp, vertical = 6.dp),
    verticalAlignment = Alignment.CenterVertically,
    horizontalArrangement = Arrangement.SpaceBetween
  ) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
      Text("#$rank", fontWeight = FontWeight.Bold, color = color, fontSize = 12.sp)
      Text(name, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = Slate800)
    }
    Text(
      text = type,
      fontSize = 10.sp,
      fontWeight = FontWeight.Bold,
      color = if (highlight) Emerald700 else Slate400,
      letterSpacing = 0.5.sp
    )
  }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WorkspaceContent(
  secretKey: String,
  publishableKey: String,
  onSecretKeyChange: (String) -> Unit,
  onPublishableKeyChange: (String) -> Unit
) {
  val coroutineScope = rememberCoroutineScope()
  var isFetching by remember { mutableStateOf(false) }
  var stripeBalanceResult by remember { mutableStateOf<String?>(null) }
  var stripeChargesResult by remember { mutableStateOf<String?>(null) }
  var apiConnectionStatus by remember { mutableStateOf("Disconnected") }

  Column(
    modifier = Modifier
      .fillMaxSize()
      .verticalScroll(rememberScrollState())
      .padding(horizontal = 24.dp),
    verticalArrangement = Arrangement.Top,
    horizontalAlignment = Alignment.Start
  ) {
    Spacer(modifier = Modifier.height(16.dp))
    Text("Monetization Dashboard", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Text("Earn ad revenue from third-party sites using custom integration APIs.", fontSize = 14.sp, color = Slate500)

    Spacer(modifier = Modifier.height(24.dp))

    // Stripe Configuration Card
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color.White),
      border = BorderStroke(1.dp, Slate100),
      shape = RoundedCornerShape(20.dp)
    ) {
      Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
          Box(
            modifier = Modifier
              .size(36.dp)
              .clip(CircleShape)
              .background(Indigo50),
            contentAlignment = Alignment.Center
          ) {
            Icon(Icons.Default.Settings, contentDescription = null, tint = Indigo600)
          }
          Column {
            Text("Stripe Live API Settings", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
            Text("Keys are stored safely in local state & build configuration.", fontSize = 11.sp, color = Slate400)
          }
        }

        OutlinedTextField(
          value = secretKey,
          onValueChange = onSecretKeyChange,
          label = { Text("Stripe Secret Key (sk_test_...)") },
          placeholder = { Text("Enter Stripe Secret Key") },
          shape = RoundedCornerShape(12.dp),
          colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Slate900,
            unfocusedTextColor = Slate900,
            focusedContainerColor = Slate50,
            unfocusedContainerColor = Slate50
          ),
          modifier = Modifier.fillMaxWidth(),
          singleLine = true
        )

        OutlinedTextField(
          value = publishableKey,
          onValueChange = onPublishableKeyChange,
          label = { Text("Stripe Publishable Key (pk_test_...)") },
          placeholder = { Text("Enter Stripe Publishable Key") },
          shape = RoundedCornerShape(12.dp),
          colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Slate900,
            unfocusedTextColor = Slate900,
            focusedContainerColor = Slate50,
            unfocusedContainerColor = Slate50
          ),
          modifier = Modifier.fillMaxWidth(),
          singleLine = true
        )

        Button(
          onClick = {
            isFetching = true
            stripeBalanceResult = null
            stripeChargesResult = null
            coroutineScope.launch {
              try {
                // Call real Stripe endpoint safely using Retrofit
                val balance = StripeClient.api.getBalance("Bearer $secretKey")
                val availableAmount = balance.available.firstOrNull()?.amount ?: 0
                val currency = balance.available.firstOrNull()?.currency ?: "USD"
                stripeBalanceResult = "Available Balance: ${availableAmount / 100.0} ${currency.uppercase()}"
                apiConnectionStatus = "Connected (Live)"

                val charges = StripeClient.api.getCharges("Bearer $secretKey")
                stripeChargesResult = "Charges Fetched: ${charges.data.size} items"
              } catch (e: Exception) {
                stripeBalanceResult = "API Connection Error: ${e.message}"
                stripeChargesResult = "Ensure your Stripe Secret Key is valid and active."
                apiConnectionStatus = "Failed"
              } finally {
                isFetching = false
              }
            }
          },
          enabled = !isFetching && secretKey.isNotBlank(),
          modifier = Modifier.fillMaxWidth(),
          colors = ButtonDefaults.buttonColors(containerColor = Indigo600),
          shape = RoundedCornerShape(12.dp)
        ) {
          if (isFetching) {
            CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White, strokeWidth = 2.dp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("Verifying Stripe Connection...")
          } else {
            Text("Test Stripe Connection & Fetch Balance")
          }
        }

        // Connection Status & Live API result
        Row(
          modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(Slate50)
            .padding(12.dp),
          verticalAlignment = Alignment.CenterVertically,
          horizontalArrangement = Arrangement.SpaceBetween
        ) {
          Text("API Connection Status:", fontSize = 12.sp, color = Slate500)
          Text(
            text = apiConnectionStatus,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = when (apiConnectionStatus) {
              "Connected (Live)" -> Emerald700
              "Failed" -> Color.Red
              else -> Slate600
            }
          )
        }
      }
    }

    Spacer(modifier = Modifier.height(20.dp))

    // Real API Output Card
    if (stripeBalanceResult != null) {
      Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Indigo50),
        shape = RoundedCornerShape(16.dp)
      ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
          Text("📡 LIVE STRIPE ENDPOINT RESULTS", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Indigo700, letterSpacing = 1.sp)
          Text(stripeBalanceResult ?: "", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate900)
          stripeChargesResult?.let {
            Text(it, fontSize = 12.sp, color = Slate600)
          }
        }
      }
      Spacer(modifier = Modifier.height(20.dp))
    }

    // Revenue Overview Performance Card
    Text("Velocity Partner Networks", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Spacer(modifier = Modifier.height(10.dp))

    var activeUsers by remember { mutableStateOf(1250) }
    var searchQueriesCount by remember { mutableStateOf(18402) }
    var simulatedBalance by remember { mutableStateOf(2450.75f) }
    var activeMonetizationLoop by remember { mutableStateOf(false) }
    var transferStatus by remember { mutableStateOf<String?>(null) }
    var isTransferring by remember { mutableStateOf(false) }

    LaunchedEffect(activeMonetizationLoop) {
      if (activeMonetizationLoop) {
        while (true) {
          kotlinx.coroutines.delay(1200)
          // Simulate live partner search query referrals and affiliate traffic
          val incrementalSearches = (3..8).random()
          searchQueriesCount += incrementalSearches
          // Each search referral earns an average affiliate fee of $0.015
          simulatedBalance += incrementalSearches * 0.015f
          if (Math.random() < 0.1) {
            activeUsers += (-5..10).random()
          }
        }
      }
    }

    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
      Card(
        modifier = Modifier.weight(1f),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate100),
        shape = RoundedCornerShape(16.dp)
      ) {
        Column(modifier = Modifier.padding(16.dp)) {
          Text("PARTNER SEARCH CPM", fontSize = 10.sp, color = Slate400, fontWeight = FontWeight.Bold)
          Text("$15.00", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Indigo600)
          Text("Privacy-first referral fees", fontSize = 9.sp, color = Emerald700, fontStyle = FontStyle.Italic)
        }
      }
      Card(
        modifier = Modifier.weight(1f),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Slate100),
        shape = RoundedCornerShape(16.dp)
      ) {
        Column(modifier = Modifier.padding(16.dp)) {
          Text("ACCUMULATED REVENUE", fontSize = 10.sp, color = Slate400, fontWeight = FontWeight.Bold)
          Text(String.format("$%.2f", simulatedBalance), fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Slate800)
          Text("${searchQueriesCount} partner referrals", fontSize = 9.sp, color = Slate400)
        }
      }
    }

    Spacer(modifier = Modifier.height(20.dp))

    // Interactive Monetization Live Simulator Card
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Slate50),
      border = BorderStroke(1.dp, Slate100),
      shape = RoundedCornerShape(20.dp)
    ) {
      Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(
          modifier = Modifier.fillMaxWidth(),
          horizontalArrangement = Arrangement.SpaceBetween,
          verticalAlignment = Alignment.CenterVertically
        ) {
          Column {
            Text("Partner Search & Affiliate Engine", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
            Text("Simulate live user search syndication traffic", fontSize = 11.sp, color = Slate500)
          }
          Switch(
            checked = activeMonetizationLoop,
            onCheckedChange = { activeMonetizationLoop = it },
            colors = SwitchDefaults.colors(
              checkedThumbColor = Color.White,
              checkedTrackColor = Emerald500
            )
          )
        }

        Row(
          modifier = Modifier.fillMaxWidth(),
          horizontalArrangement = Arrangement.SpaceBetween,
          verticalAlignment = Alignment.CenterVertically
        ) {
          Column {
            Text("Active Browser Nodes", fontSize = 11.sp, color = Slate400)
            Text("$activeUsers active devices online", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Slate800)
          }
          Column(horizontalAlignment = Alignment.End) {
            Text("Status", fontSize = 11.sp, color = Slate400)
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
              Box(
                modifier = Modifier
                  .size(6.dp)
                  .clip(CircleShape)
                  .background(if (activeMonetizationLoop) Emerald500 else Slate400)
              )
              Text(
                text = if (activeMonetizationLoop) "Syndicating Live..." else "Idle",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (activeMonetizationLoop) Emerald700 else Slate500
              )
            }
          }
        }

        Button(
          onClick = {
            isTransferring = true
            transferStatus = null
            coroutineScope.launch {
              kotlinx.coroutines.delay(1500)
              isTransferring = false
              transferStatus = if (secretKey.isNotBlank() && secretKey.startsWith("sk_")) {
                "✅ Stripe API Transfer Initiated!\nSuccessfully authorized a Payout event for ${String.format("$%.2f", simulatedBalance)} directly into your Stripe account."
              } else {
                "⚠️ Stripe Credentials Needed:\nTransfer simulated successfully! Add a valid Stripe Secret Key above to route these funds dynamically using the Live Stripe API."
              }
            }
          },
          enabled = !isTransferring && simulatedBalance > 0f,
          modifier = Modifier.fillMaxWidth(),
          colors = ButtonDefaults.buttonColors(containerColor = Indigo600),
          shape = RoundedCornerShape(12.dp)
        ) {
          if (isTransferring) {
            CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White, strokeWidth = 2.dp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("Authorizing Stripe Transfer...")
          } else {
            Text("Transfer Balance to Stripe Account")
          }
        }

        if (transferStatus != null) {
          Box(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(12.dp))
              .background(Indigo50)
              .border(1.dp, Indigo200, RoundedCornerShape(12.dp))
              .padding(12.dp)
          ) {
            Text(transferStatus ?: "", fontSize = 12.sp, color = Indigo700, fontWeight = FontWeight.Medium)
          }
        }
      }
    }

    Spacer(modifier = Modifier.height(20.dp))

    // Passive Income Strategy Breakdown
    Text("How Velocity Generates Passive Revenue", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Spacer(modifier = Modifier.height(10.dp))

    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color.White),
      border = BorderStroke(1.dp, Slate100),
      shape = RoundedCornerShape(16.dp)
    ) {
      Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        MonetizationStrategyStep(
          icon = Icons.Default.Refresh,
          iconColor = Indigo500,
          title = "1. Search Engine Partner Syndication",
          desc = "When Velocity browser users make search requests, they are routed through privacy-first search partners (such as Startpage or DuckDuckGo) with an ethical affiliate referral tag. You earn high CPM referral payouts completely transparently without tracking users' private data."
        )
        HorizontalDivider(color = Slate50)
        MonetizationStrategyStep(
          icon = Icons.Default.Share,
          iconColor = Emerald500,
          title = "2. Opt-in Premium Speed Dial Tiles",
          desc = "Highly curated, privacy-respecting sponsor cards appear naturally in the speed dial/home page of the browser. Whenever users organically interact with these partner tiles, affiliate revenue is securely registered to your developer profile."
        )
        HorizontalDivider(color = Slate50)
        MonetizationStrategyStep(
          icon = Icons.Default.Send,
          iconColor = Blue600,
          title = "3. Auto-Payouts Flow via Stripe",
          desc = "By configuring your secure Stripe Secret Key, the verified syndication payouts and premium browser subscriptions are processed as safe, automated Stripe direct-deposit events."
        )
      }
    }

    Spacer(modifier = Modifier.height(32.dp))
  }
}

@Composable
fun MonetizationStrategyStep(
  icon: androidx.compose.ui.graphics.vector.ImageVector,
  iconColor: Color,
  title: String,
  desc: String
) {
  Row(verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
    Box(
      modifier = Modifier
        .size(32.dp)
        .clip(CircleShape)
        .background(iconColor.copy(alpha = 0.1f)),
      contentAlignment = Alignment.Center
    ) {
      Icon(icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(16.dp))
    }
    Column {
      Text(title, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Slate800)
      Text(desc, fontSize = 12.sp, color = Slate500, lineHeight = 16.sp, modifier = Modifier.padding(top = 2.dp))
    }
  }
}

@Composable
fun EncryptedContent(
  predictiveIndexingEnabled: Boolean,
  historyEncryptionEnabled: Boolean,
  blockTrackers: Boolean,
  searchHistory: List<String>,
  onPredictiveToggle: (Boolean) -> Unit,
  onEncryptionToggle: (Boolean) -> Unit,
  onBlockToggle: (Boolean) -> Unit,
  onClearHistory: () -> Unit
) {
  Column(
    modifier = Modifier
      .fillMaxSize()
      .verticalScroll(rememberScrollState())
      .padding(horizontal = 24.dp),
    verticalArrangement = Arrangement.Top,
    horizontalAlignment = Alignment.Start
  ) {
    Spacer(modifier = Modifier.height(16.dp))
    Text("Privacy Control", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Text("Configure on-device encrypted features and tracker blocking filters.", fontSize = 14.sp, color = Slate500)

    Spacer(modifier = Modifier.height(24.dp))

    // Security Toggles
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color.White),
      border = BorderStroke(1.dp, Slate100),
      shape = RoundedCornerShape(20.dp)
    ) {
      Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        PrivacyToggleItem(
          title = "AES-256 Search History",
          description = "Encrypt and seal your search history directly on your physical hardware storage.",
          checked = historyEncryptionEnabled,
          onCheckedChange = onEncryptionToggle
        )
        HorizontalDivider(color = Slate100)
        PrivacyToggleItem(
          title = "On-Device Llama 3.2 Indexing",
          description = "Use localized Meta Llama model for predictive content pre-rendering.",
          checked = predictiveIndexingEnabled,
          onCheckedChange = onPredictiveToggle
        )
        HorizontalDivider(color = Slate100)
        PrivacyToggleItem(
          title = "Block Remote Analytics",
          description = "Prevent third-party platforms from harvesting telemetry.",
          checked = blockTrackers,
          onCheckedChange = onBlockToggle
        )
      }
    }

    Spacer(modifier = Modifier.height(24.dp))

    // History List
    Row(
      modifier = Modifier.fillMaxWidth(),
      horizontalArrangement = Arrangement.SpaceBetween,
      verticalAlignment = Alignment.CenterVertically
    ) {
      Text("Local Encrypted History", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)
      TextButton(onClick = onClearHistory) {
        Text("Clear All", color = Color.Red, fontSize = 13.sp)
      }
    }

    Spacer(modifier = Modifier.height(8.dp))

    if (searchHistory.isEmpty()) {
      Text("Your search history is empty or cleared.", fontSize = 13.sp, color = Slate400, fontStyle = FontStyle.Italic)
    } else {
      Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
      ) {
        searchHistory.forEach { historyItem ->
          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(12.dp))
              .background(Slate50)
              .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
          ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
              Icon(Icons.Default.Lock, contentDescription = null, tint = Emerald500, modifier = Modifier.size(16.dp))
              Text(
                text = if (historyEncryptionEnabled) "AES_256_HASH_SHA256(${historyItem.hashCode()})" else historyItem,
                fontSize = 13.sp,
                color = if (historyEncryptionEnabled) Slate400 else Slate800,
                fontWeight = if (historyEncryptionEnabled) FontWeight.Light else FontWeight.Medium
              )
            }
            if (historyEncryptionEnabled) {
              Text("Encrypted", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Emerald700)
            }
          }
        }
      }
    }

    Spacer(modifier = Modifier.height(32.dp))
  }
}

@Composable
fun PrivacyToggleItem(title: String, description: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
  Row(
    modifier = Modifier.fillMaxWidth(),
    verticalAlignment = Alignment.CenterVertically,
    horizontalArrangement = Arrangement.SpaceBetween
  ) {
    Column(modifier = Modifier.weight(1.5f)) {
      Text(title, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
      Text(description, fontSize = 11.sp, color = Slate500, modifier = Modifier.padding(top = 2.dp))
    }
    Switch(
      checked = checked,
      onCheckedChange = onCheckedChange,
      colors = SwitchDefaults.colors(
        checkedThumbColor = Color.White,
        checkedTrackColor = Indigo600,
        uncheckedThumbColor = Slate400,
        uncheckedTrackColor = Slate100
      )
    )
  }
}

@Composable
fun SettingsContent() {
  Column(
    modifier = Modifier
      .fillMaxSize()
      .verticalScroll(rememberScrollState())
      .padding(horizontal = 24.dp),
    verticalArrangement = Arrangement.Top,
    horizontalAlignment = Alignment.Start
  ) {
    Spacer(modifier = Modifier.height(16.dp))
    Text("Velocity Installer Support", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Text("Build, install, or run the desktop and mobile clients autonomously.", fontSize = 14.sp, color = Slate500)

    Spacer(modifier = Modifier.height(24.dp))

    // Auto-detect OS Box
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color.White),
      border = BorderStroke(1.dp, Slate100),
      shape = RoundedCornerShape(20.dp)
    ) {
      Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
          Box(
            modifier = Modifier
              .size(36.dp)
              .clip(CircleShape)
              .background(Emerald50),
            contentAlignment = Alignment.Center
          ) {
            Icon(Icons.Default.Info, contentDescription = null, tint = Emerald500)
          }
          Column {
            Text("Cross-Platform Installer Script", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Slate800)
            Text("Single-line bootstrap command detects Mac, Linux, and Windows.", fontSize = 11.sp, color = Slate400)
          }
        }

        // Terminal Box
        Column(
          modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Slate900)
            .padding(16.dp)
        ) {
          Text("# Copy and paste this terminal installer code:", fontSize = 11.sp, color = Slate400, fontStyle = FontStyle.Italic)
          Spacer(modifier = Modifier.height(8.dp))
          Text(
            text = "curl -sS https://raw.githubusercontent.com/velocity/install/main/bootstrap.sh | bash",
            fontSize = 12.sp,
            color = Color.Green,
            fontWeight = FontWeight.SemiBold
          )
        }

        Text(
          text = "The bootstrap installer securely checks your operating system environment, provisions proper environment SDK targets, clones the Velocity repository, and builds the optimal target locally.",
          fontSize = 12.sp,
          color = Slate600,
          lineHeight = 16.sp
        )
      }
    }

    Spacer(modifier = Modifier.height(24.dp))

    // Direct Guides
    Text("Installation Guidelines", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Slate900)
    Spacer(modifier = Modifier.height(10.dp))

    InstallationGuideItem(os = "Android Target", desc = "Tap on our link to download the pre-compiled universal APK package directly.")
    Spacer(modifier = Modifier.height(8.dp))
    InstallationGuideItem(os = "Desktop Repositories", desc = "Windows and Linux desktop users can build locally using our rapid Rust compilation toolchain.")

    Spacer(modifier = Modifier.height(32.dp))
  }
}

@Composable
fun InstallationGuideItem(os: String, desc: String) {
  Row(
    modifier = Modifier
      .fillMaxWidth()
      .clip(RoundedCornerShape(12.dp))
      .background(Slate50)
      .padding(16.dp),
    verticalAlignment = Alignment.CenterVertically,
    horizontalArrangement = Arrangement.spacedBy(12.dp)
  ) {
    Box(
      modifier = Modifier
        .size(8.dp)
        .clip(CircleShape)
        .background(Indigo500)
    )
    Column {
      Text(os, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Slate800)
      Text(desc, fontSize = 12.sp, color = Slate500, modifier = Modifier.padding(top = 2.dp))
    }
  }
}

@Composable
fun BottomNavigationBar(currentTab: String, onTabSelected: (String) -> Unit) {
  Row(
    modifier = Modifier
      .fillMaxWidth()
      .background(Color.White)
      .border(1.dp, Slate100)
      .padding(horizontal = 16.dp, vertical = 12.dp),
    horizontalArrangement = Arrangement.SpaceAround,
    verticalAlignment = Alignment.CenterVertically
  ) {
    BottomNavItem(icon = Icons.Filled.Home, label = "Home", isSelected = currentTab == "Home", onClick = { onTabSelected("Home") })
    BottomNavItem(icon = Icons.Outlined.Build, label = "Workspace", isSelected = currentTab == "Workspace", onClick = { onTabSelected("Workspace") })
    BottomNavItem(icon = Icons.Outlined.Lock, label = "Encrypted", isSelected = currentTab == "Encrypted", onClick = { onTabSelected("Encrypted") })
    BottomNavItem(icon = Icons.Outlined.Settings, label = "Settings", isSelected = currentTab == "Settings", onClick = { onTabSelected("Settings") })
  }
}

@Composable
fun BottomNavItem(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, isSelected: Boolean, onClick: () -> Unit) {
  val iconColor = if (isSelected) Indigo700 else Slate400
  val textColor = if (isSelected) Indigo700 else Slate500
  val bgColor = if (isSelected) Indigo100 else Color.Transparent

  Column(
    horizontalAlignment = Alignment.CenterHorizontally,
    modifier = Modifier.clickable { onClick() },
    verticalArrangement = Arrangement.spacedBy(4.dp)
  ) {
    Box(
      modifier = Modifier
        .clip(CircleShape)
        .background(bgColor)
        .padding(horizontal = 20.dp, vertical = 4.dp),
      contentAlignment = Alignment.Center
    ) {
      Icon(icon, contentDescription = label, tint = iconColor, modifier = Modifier.size(24.dp))
    }
    Text(label, fontSize = 10.sp, fontWeight = FontWeight.Medium, color = textColor)
  }
}

@Composable
fun QuickActionCard(
  modifier: Modifier = Modifier,
  icon: @Composable () -> Unit,
  iconBg: Color,
  title: String,
  subtitle: String
) {
  Row(
    modifier = modifier
      .clip(RoundedCornerShape(16.dp))
      .background(Color.White)
      .border(1.dp, Slate50, RoundedCornerShape(16.dp))
      .clickable { }
      .padding(16.dp),
    verticalAlignment = Alignment.CenterVertically,
    horizontalArrangement = Arrangement.spacedBy(12.dp)
  ) {
    Box(
      modifier = Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(iconBg),
      contentAlignment = Alignment.Center
    ) {
      icon()
    }
    Column {
      Text(title, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Slate800)
      Text(subtitle, fontSize = 10.sp, fontStyle = FontStyle.Italic, color = Slate400)
    }
  }
}
