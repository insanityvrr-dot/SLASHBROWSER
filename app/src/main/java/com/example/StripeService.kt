package com.example

import com.squareup.moshi.JsonClass
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.GET
import retrofit2.http.Header

@JsonClass(generateAdapter = true)
data class StripeBalance(
    val available: List<BalanceAmount>,
    val pending: List<BalanceAmount>
)

@JsonClass(generateAdapter = true)
data class BalanceAmount(
    val amount: Long,
    val currency: String
)

@JsonClass(generateAdapter = true)
data class StripeTransaction(
    val id: String,
    val amount: Long,
    val currency: String,
    val status: String,
    val description: String?,
    val created: Long
)

@JsonClass(generateAdapter = true)
data class StripeTransactionsResponse(
    val data: List<StripeTransaction>
)

interface StripeApi {
    @GET("v1/balance")
    suspend fun getBalance(
        @Header("Authorization") authHeader: String
    ): StripeBalance

    @GET("v1/charges")
    suspend fun getCharges(
        @Header("Authorization") authHeader: String
    ): StripeTransactionsResponse
}

object StripeClient {
    private val retrofit = Retrofit.Builder()
        .baseUrl("https://api.stripe.com/")
        .addConverterFactory(MoshiConverterFactory.create())
        .build()

    val api: StripeApi = retrofit.create(StripeApi::class.java)
}
